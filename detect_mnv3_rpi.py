import time
import cv2
import torch
import numpy as np
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_320_fpn
from torchvision.utils import draw_bounding_boxes
from cv2 import VideoWriter, VideoWriter_fourcc
from picamera2 import Picamera2

labels_names_dict = {
	1: 'closed_pan',
	2: 'closed_pot',
	3: 'closed_pot_boiling',
	4: 'dish',
	5: 'fire',
	6: 'gas',
	7: 'human',
	8: 'open_pot',
	9: 'open_pot_boiling',
	10: 'other',
	11: 'pan',
	12: 'other'
}

device = torch.device(
	'cuda') if torch.cuda.is_available() else torch.device('cpu')

model = fasterrcnn_mobilenet_v3_large_320_fpn(box_score_thresh=0.8)
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
	main={"format": 'RGB888', "size": (1920, 1080)}))

picam2.start()

# Inicjalizacja VideoWriter
fourcc = VideoWriter_fourcc(*'MJPG')  # Wybierz kodek wideo
# '30' to ilość klatek na sekundę
out = VideoWriter('filename.avi', fourcc, 30, (1920, 1080))

checkpoint = torch.load("kss-frcnnmnv3-320-v7.ckpt", map_location=torch.device('cpu'))
state_dict = checkpoint["state_dict"]

new_state_dict = {}
for key, value in state_dict.items():
	if key.startswith('model.'):
		new_key = key[len('model.'):]
		new_state_dict[new_key] = value
	else:
		new_state_dict[key] = value

state_dict = new_state_dict

model.load_state_dict(state_dict)
model.eval()
model = torch.jit.script(model)

started = time.time()
last_logged = time.time()
frame_count = 0

while True:
	im = picam2.capture_array()

	if not im.any():
		continue

	im = cv2.resize(im, (640, 640), interpolation=cv2.INTER_AREA)
	im = cv2.transpose(im)
	im = np.transpose(im, (2, 0, 1))

	im_tensor = torch.from_numpy(im)
	normalized = torch.div(im_tensor, torch.max(im_tensor))
	normalized = normalized.to(device)
	imgs = [normalized]
	losses, detections = model(imgs)

	for prediction in detections:
		label_ids = [label_id.item() for label_id in prediction['labels']]
		labels_names = [labels_names_dict[label_id] for label_id in label_ids]
		box = draw_bounding_boxes(
			im_tensor,
			boxes=prediction['boxes'],
			labels=labels_names,
			colors='red',
			width=4,
			font_size=30
		)
	image_array = np.transpose(box.detach().numpy(), (1, 2, 0))
	#out.write(image_array)
	cv2.imwrite('color_img.png', image_array)
	# log model performance
	frame_count += 1
	now = time.time()
	if now - last_logged > 1:
		print(f"{frame_count / (now-last_logged)} fps")
		last_logged = now
		frame_count = 0
