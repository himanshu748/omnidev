import sys, time
import Vision
from Quartz import CIImage, CFURLCreateWithFileSystemPath, kCFURLPOSIXPathStyle
from Foundation import NSURL

def ocr(path):
    url = NSURL.fileURLWithPath_(path)
    ci = CIImage.imageWithContentsOfURL_(url)
    if ci is None:
        return None, "unreadable"
    handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(ci, None)
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(0)  # accurate
    ok, err = handler.performRequests_error_([req], None)
    if not ok:
        return None, str(err)
    lines = []
    for obs in (req.results() or []):
        top = obs.topCandidates_(1)
        if top and len(top):
            lines.append(top[0].string())
    return "\n".join(lines), None

path = sys.argv[1]
t0 = time.time()
text, err = ocr(path)
dt = (time.time() - t0) * 1000
if err:
    print("ERROR:", err)
else:
    print(f"OCR ok in {dt:.0f} ms, {len(text)} chars, {len(text.splitlines())} lines")
    print("--- first 300 chars ---")
    print(text[:300])
