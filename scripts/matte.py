"""Matte orang (selfie segmenter) + guided filter untuk tepi rambut. Guna: import get_matte"""
import numpy as np, cv2, mediapipe as mp
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision

_seg = None
def _get():
    global _seg
    if _seg is None:
        opt = vision.ImageSegmenterOptions(
            base_options=mpp.BaseOptions(model_asset_path='work/models/selfie_segmenter.tflite'),
            output_confidence_masks=True, output_category_mask=False)
        _seg = vision.ImageSegmenter.create_from_options(opt)
    return _seg

def guided(I, p, r, eps):
    k = (2*r+1, 2*r+1)
    mI = cv2.boxFilter(I, -1, k); mp_ = cv2.boxFilter(p, -1, k)
    cov = cv2.boxFilter(I*p, -1, k) - mI*mp_
    var = cv2.boxFilter(I*I, -1, k) - mI*mI
    a = cov/(var+eps); b = mp_ - a*mI
    return cv2.boxFilter(a, -1, k)*I + cv2.boxFilter(b, -1, k)

def get_matte(rgb):
    """rgb uint8 HxWx3 (1080x1920) -> float matte HxW 0..1"""
    H, W = rgb.shape[:2]
    small = cv2.resize(rgb, (W//2, H//2), interpolation=cv2.INTER_AREA)
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(small))
    m = _get().segment(img).confidence_masks[0].numpy_view().astype(np.float32)
    m = cv2.resize(m, (W//2, H//2), interpolation=cv2.INTER_LINEAR)
    g = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    m = np.clip(guided(g, m, 8, 1e-3), 0, 1)
    m = np.clip((m-0.35)/0.4, 0, 1)            # kontras tepi
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    return m
