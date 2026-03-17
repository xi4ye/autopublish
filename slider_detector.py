"""
滑块缺口检测模块 - 使用ddddocr
基于分析结果，ddddocr返回的target_x需要加上约19px的偏移
"""
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import random
import ddddocr

_ddddocr_instance = None

def get_ddddocr():
    global _ddddocr_instance
    if _ddddocr_instance is None:
        _ddddocr_instance = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    return _ddddocr_instance


def detect_gap_by_ddddocr(bg_content, slider_content, initx=60):
    """使用ddddocr检测缺口"""
    try:
        if not bg_content or not slider_content:
            print("ddddocr检测失败: 图片内容为空")
            return None
        
        if len(bg_content) < 100 or len(slider_content) < 100:
            print(f"ddddocr检测失败: 图片内容太小 bg={len(bg_content)}, slider={len(slider_content)}")
            return None
        
        ocr = get_ddddocr()
        res = ocr.slide_match(slider_content, bg_content, simple_target=False)
        
        if not res or 'target' not in res:
            print(f"ddddocr检测失败: 返回结果无效 {res}")
            return None
        
        target_x = res['target'][0]
        
        try:
            slider_img = Image.open(BytesIO(slider_content))
            slider_width = slider_img.size[0]
        except Exception:
            slider_width = 60
        
        distance = target_x - initx + 19
        
        print(f"  ddddocr检测: target_x={target_x}, initx={initx}, distance={distance}")
        return distance
    except Exception as e:
        print(f"ddddocr检测失败: {e}")
        return None


def detect_gap_by_brightness(bg_content, initx=60):
    """通过亮度变化检测缺口"""
    try:
        if not bg_content or len(bg_content) < 100:
            print("亮度检测失败: 图片内容为空或太小")
            return None
        
        bg_img = Image.open(BytesIO(bg_content))
        bg_array = np.array(bg_img)
        
        if bg_array.size == 0:
            print("亮度检测失败: 图片数组为空")
            return None
        
        if len(bg_array.shape) == 3:
            bg_gray = cv2.cvtColor(bg_array, cv2.COLOR_RGB2GRAY)
        else:
            bg_gray = bg_array
        
        brightness = []
        for x in range(bg_gray.shape[1]):
            col_mean = np.mean(bg_gray[:, x])
            brightness.append((x, col_mean))
        
        diffs = []
        for i in range(initx + 10, len(brightness) - 10):
            left_mean = np.mean([b for _, b in brightness[i-10:i]])
            right_mean = np.mean([b for _, b in brightness[i:i+10]])
            diff = abs(right_mean - left_mean)
            diffs.append((brightness[i][0], diff))
        
        if not diffs:
            return None
        
        sorted_diffs = sorted(diffs, key=lambda d: d[1], reverse=True)
        
        valid_positions = [(x, d) for x, d in sorted_diffs if 130 <= x - initx <= 200]
        
        if valid_positions:
            best_x = valid_positions[0][0]
        else:
            best_x = sorted_diffs[0][0]
        
        distance = best_x - initx
        print(f"  亮度检测: best_x={best_x}, initx={initx}, distance={distance}")
        return distance
    except Exception as e:
        print(f"亮度检测失败: {e}")
        return None


def get_distance_with_retry(bg_content, slider_content=None, initx=60, max_attempts=15):
    """获取距离，支持多次尝试不同值"""
    results = []
    
    if slider_content and len(slider_content) > 100:
        dist_ddddocr = detect_gap_by_ddddocr(bg_content, slider_content, initx)
        if dist_ddddocr:
            results.append(dist_ddddocr)
            for offset in [-5, 5, -10, 10, -15, 15, -20, 20]:
                results.append(dist_ddddocr + offset)
    
    dist_brightness = detect_gap_by_brightness(bg_content, initx)
    if dist_brightness:
        results.append(dist_brightness)
        for offset in [-5, 5, -10, 10]:
            results.append(dist_brightness + offset)
    
    # 添加随机距离作为后备
    for r in [random.randint(130, 180) for _ in range(5)]:
        results.append(r)
    
    # 去重并保持顺序
    unique_distances = list(dict.fromkeys(results))
    
    return unique_distances[:max_attempts]


if __name__ == "__main__":
    print("滑块检测器已加载")
