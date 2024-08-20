from PIL import Image

from ultralytics import YOLO

# Load a pretrained YOLOv8n model
model = YOLO("C:/source/models/taihanfiber_2-1_best.pt")

# Run inference on 'bus.jpg'
results = model(["C:/image/20240819/Original/130458.jpg", "C:/image/20240819/Original/130041.jpg"])  # results list

# Visualize the results
for i, r in enumerate(results):
    # Plot results image
    im_bgr = r.plot()  # BGR-order numpy array
    im_rgb = Image.fromarray(im_bgr[..., ::-1])  # RGB-order PIL image

    # Show results to screen (in supported environments)
    r.show()

    # Save results to disk
    r.save(filename=f"results{i}.jpg")

