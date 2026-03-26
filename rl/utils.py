import cv2

def render(state):
    img = state["image"]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    cv2.imshow("ALFRED", img)
    cv2.waitKey(1)