#!/usr/bin/env python3
import argparse, cv2

def grab(dev):
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", default="/dev/video2")
    ap.add_argument("--dict", default="DICT_4X4_50")
    args = ap.parse_args()

    if not hasattr(cv2, "aruco"):
        raise SystemExit("ERROR: cv2.aruco missing")

    aruco = cv2.aruco
    dict_id = getattr(aruco, args.dict, None)
    if dict_id is None:
        raise SystemExit(f"ERROR: unknown dict {args.dict}")

    frame = grab(args.dev)
    if frame is None:
        raise SystemExit(f"ERROR: no frame from {args.dev}")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    d = aruco.getPredefinedDictionary(dict_id)
    p = aruco.DetectorParameters()
    corners, ids, _ = aruco.detectMarkers(gray, d, parameters=p)

    print("DEV", args.dev, "FRAME", frame.shape, "MARKERS", 0 if ids is None else len(ids), "IDS", None if ids is None else ids.flatten().tolist())

if __name__ == "__main__":
    main()
