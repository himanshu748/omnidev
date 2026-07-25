import time, statistics
import Vision
from Quartz import CIImage
from Foundation import NSURL

def ocr(path):
    ci = CIImage.imageWithContentsOfURL_(NSURL.fileURLWithPath_(path))
    h = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(ci, None)
    r = Vision.VNRecognizeTextRequest.alloc().init()
    r.setRecognitionLevel_(0)
    h.performRequests_error_([r], None)
    return sum(len(o.topCandidates_(1)[0].string()) for o in (r.results() or []))

ocr("/tmp/ocr_test.png")  # warm
times = []
for _ in range(12):
    t0 = time.perf_counter()
    ocr("/tmp/ocr_test.png")
    times.append((time.perf_counter() - t0) * 1000)
print(f"warm OCR: median {statistics.median(times):.0f} ms, min {min(times):.0f}, max {max(times):.0f}")
print(f"projected 1,200 screenshots: {statistics.median(times)*1200/1000/60:.1f} min single-threaded")
