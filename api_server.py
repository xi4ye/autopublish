# -*- coding: utf-8 -*-
import asyncio
import json
import os
from datetime import datetime
from aiohttp import web
from typing import Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# 导入主处理函数
from create_detailed_news_template import TemplateStyle, SmartImageGenerator
from create_template import create_template
from fenmian import create_soft_shadow_border as create_fenmian
from data_adapter import format_for_template
from translate_formatted import translate_formatted_json
from autowx import wx_main

# 配置 - 从环境变量读取
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None
    auto_publish: bool = False


class TaskQueue:
    def __init__(self, max_workers: int = 2):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.tasks: Dict[str, Task] = {}
        self.max_workers = max_workers
        self.workers: list = []
        self._running = False
    
    async def add_task(self, task_id: str, data: Dict[str, Any], auto_publish: bool = False) -> Task:
        task = Task(id=task_id, data=data, auto_publish=auto_publish)
        self.tasks[task_id] = task
        await self.queue.put(task_id)
        print(f"[队列] 任务 {task_id} 已加入队列，当前队列长度: {self.queue.qsize()}")
        return task
    
    def get_task(self, task_id: str) -> Task:
        return self.tasks.get(task_id)
    
    async def start_workers(self):
        if self._running:
            return
        self._running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i + 1))
            self.workers.append(worker)
        print(f"[队列] 已启动 {self.max_workers} 个工作进程")
    
    async def stop_workers(self):
        self._running = False
        for worker in self.workers:
            worker.cancel()
        self.workers.clear()
        print("[队列] 工作进程已停止")
    
    async def _worker(self, worker_id: int):
        print(f"[Worker-{worker_id}] 已启动")
        while self._running:
            try:
                task_id = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                task = self.tasks.get(task_id)
                if not task:
                    continue
                
                print(f"[Worker-{worker_id}] 开始处理任务 {task_id}")
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now()
                
                try:
                    result = await process_news_data(task.data, task.auto_publish)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    print(f"[Worker-{worker_id}] 任务 {task_id} 处理完成")
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    print(f"[Worker-{worker_id}] 任务 {task_id} 处理失败: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    task.completed_at = datetime.now()
                    self.queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Worker-{worker_id}] 错误: {e}")
        print(f"[Worker-{worker_id}] 已停止")


task_queue = TaskQueue(max_workers=2)


async def process_news_data(data, auto_publish=False):
    """处理接收到的新闻数据"""
    print("=" * 60)
    print("开始处理新闻数据")
    print("=" * 60)
    
    print(f"\n接收到记录: ID={data.get('id')}")
    description = data.get('description', '')
    if description:
        print(f"标题: {description[:50]}...")
    
    print("\n开始处理数据...")
    
    print("\n第一步：格式化数据（先提取字段，不翻译）")
    formatted_data = format_for_template(data, resolve_urls=False)
    
    print(f"\n格式化结果:")
    print(f"  - COLLECTION: {len(formatted_data['COLLECTION'])} 条")
    print(f"  - ANALYSIS.evidence: {len(formatted_data['ANALYSIS']['evidence'])} 条")
    print(f"  - CONCLUSION.DetailedReasons: {len(formatted_data['CONCLUSION']['DetailedReasons'])} 条")
    print(f"  - FinalJudgment: {formatted_data['CONCLUSION']['FinalJudgment']}")
    
    print("\n第二步：翻译格式化后的数据")
    translated_data = translate_formatted_json(formatted_data)
    
    print(f"\n翻译结果:")
    print(f"  - COLLECTION: {len(translated_data['COLLECTION'])} 条")
    print(f"  - ANALYSIS.evidence: {len(translated_data['ANALYSIS']['evidence'])} 条")
    print(f"  - CONCLUSION.DetailedReasons: {len(translated_data['CONCLUSION']['DetailedReasons'])} 条")
    
    formatted_data = translated_data
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    translated_file = f"data/formated_translated_{timestamp}.json"
    with open(translated_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 格式化完成，保存到: {translated_file}")
    
    print("\n" + "=" * 60)
    print("生成海报")
    print("=" * 60)
    
    title = formatted_data['description']
    
    generator = SmartImageGenerator(external_data=formatted_data)
    generator.generate_image(
        style=TemplateStyle.TECH,
        output_path=f"output/image2_{timestamp}.png"
    )
    
    _, cover_jr = create_fenmian(
        border_width=40,
        margin=40,
        font_size=42,
        main_text=title,
        text_top_margin=30,
        text_left_margin=30,
        special_font_size=42,
        platform='jr',
        timestamp=timestamp
    )
    
    _, cover_wx = create_fenmian(
        border_width=80,
        margin=80,
        font_size=168,
        main_text=title,
        text_top_margin=100,
        text_left_margin=100,
        special_font_size=168,
        platform='wx',
        timestamp=timestamp
    )
    
    doc_path = create_template(platform='jr', timestamp=timestamp)
    
    result = {
        "status": "success",
        "id": data.get("id"),
        "timestamp": timestamp,
        "files": {
            "translated": translated_file,
            "poster": f"output/image2_{timestamp}.png",
            "cover_jr": cover_jr,
            "cover_wx": cover_wx,
            "document": doc_path
        }
    }
    
    if auto_publish:
        print("\n发布到今日头条...")
        try:
            from autojr_pydoll import auto_publish_jr
            publish_result = await auto_publish_jr(title=title, timestamp=timestamp)
            result["publish_jr"] = publish_result
        except Exception as e:
            print(f"发布到今日头条失败: {e}")
            result["publish_jr"] = {"status": "error", "message": str(e)}
        
        print("\n发布到微信公众号...")
        try:
            wx_result = wx_main(title=title, timestamp=timestamp)
            result["publish_wx"] = wx_result
        except Exception as e:
            print(f"发布到微信公众号失败: {e}")
            result["publish_wx"] = {"status": "error", "message": str(e)}
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)
    
    return result


async def handle_post(request):
    """处理 POST 请求 - 将任务加入队列"""
    try:
        data = await request.json()
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 记录请求日志
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"request_{datetime.now().strftime('%Y%m%d')}.json")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "data": data
        }
        
        # 追加写入日志文件
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        auto_publish = data.pop('auto_publish', True)
        
        print(f"\n[API] 接收到请求: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[API] 任务ID: {task_id}")
        print(f"[API] 自动发布: {auto_publish}")
        print(f"[API] 请求已记录到: {log_file}")
        
        task = await task_queue.add_task(task_id, data, auto_publish=auto_publish)
        
        return web.json_response({
            "status": "accepted",
            "task_id": task_id,
            "message": "任务已加入队列，请使用 task_id 查询处理状态",
            "queue_size": task_queue.queue.qsize(),
            "auto_publish": auto_publish
        }, status=202)
        
    except json.JSONDecodeError as e:
        print(f"[API] JSON 解析错误: {e}")
        return web.json_response({
            "status": "error",
            "message": "无效的 JSON 格式"
        }, status=400)
    except Exception as e:
        print(f"[API] 处理错误: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)


async def handle_task_status(request):
    """查询任务状态"""
    task_id = request.match_info.get('task_id', '')
    task = task_queue.get_task(task_id)
    
    if not task:
        return web.json_response({
            "status": "error",
            "message": f"任务 {task_id} 不存在"
        }, status=404)
    
    response = {
        "task_id": task.id,
        "status": task.status.value,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
    
    if task.status == TaskStatus.COMPLETED:
        response["result"] = task.result
    elif task.status == TaskStatus.FAILED:
        response["error"] = task.error
    
    return web.json_response(response)


async def handle_get(request):
    """处理 GET 请求 - 健康检查"""
    return web.json_response({
        "status": "ok",
        "service": "news_publisher",
        "timestamp": datetime.now().isoformat(),
        "queue_size": task_queue.queue.qsize(),
        "pending_tasks": sum(1 for t in task_queue.tasks.values() if t.status == TaskStatus.PENDING),
        "processing_tasks": sum(1 for t in task_queue.tasks.values() if t.status == TaskStatus.PROCESSING),
        "completed_tasks": sum(1 for t in task_queue.tasks.values() if t.status == TaskStatus.COMPLETED),
        "failed_tasks": sum(1 for t in task_queue.tasks.values() if t.status == TaskStatus.FAILED),
    })


async def handle_queue_status(request):
    """查询队列状态"""
    return web.json_response({
        "queue_size": task_queue.queue.qsize(),
        "total_tasks": len(task_queue.tasks),
        "workers": task_queue.max_workers,
        "tasks": {
            "pending": sum(1 for t in task_queue.tasks.values() if t.status == TaskStatus.PENDING),
            "processing": sum(1 for t in task_queue.tasks.values() if t.status == TaskStatus.PROCESSING),
            "completed": sum(1 for t in task_queue.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in task_queue.tasks.values() if t.status == TaskStatus.FAILED),
        }
    })


async def start_server(host='127.0.0.1', port=8888):
    """启动服务器"""
    app = web.Application()
    app.add_routes([
        web.post('/', handle_post),
        web.get('/', handle_get),
        web.post('/api/news', handle_post),
        web.get('/health', handle_get),
        web.get('/api/task/{task_id}', handle_task_status),
        web.get('/api/queue', handle_queue_status),
    ])
    
    print(f"\n" + "=" * 60)
    print("新闻发布 API 服务器 (异步队列模式)")
    print("=" * 60)
    print(f"\n服务器地址: http://{host}:{port}")
    print(f"\nAPI 端点:")
    print(f"  - POST /api/news           提交新闻数据（返回 task_id）")
    print(f"  - GET  /api/task/{{task_id}}  查询任务状态")
    print(f"  - GET  /api/queue          查询队列状态")
    print(f"  - GET  /health             健康检查")
    print(f"\n数据格式请参考: INPUT_API_DOC.md")
    print(f"\n按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")
    
    await task_queue.start_workers()
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
    finally:
        await task_queue.stop_workers()
        await runner.cleanup()

if __name__ == "__main__":
    import sys
    
    host = '127.0.0.1'
    port = 8888
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    asyncio.run(start_server(host, port))
