import warnings

# Ignore warning on production
warnings.filterwarnings("ignore")

import runpod

import torch
import os, sys, json, subprocess, requests, runpod
from diffusers.utils import load_image
import numpy as np

from scripts.gradio.i2v_test_application import Image2Video
from utils.file_utils import download_file, upload_to_s3, map_network_volume, sync_checkpoints

# Set app identity
appName = 'ToonCrafter'
bucket_name = appName

def handler(job):
    input = job['input']

    input_image1_url = input.get('input_image1_url', os.getenv('DEFAULT_INPUT_IMAGE1_URL', None))
    input_image2_url = input.get('input_image2_url', os.getenv('DEFAULT_INPUT_IMAGE2_URL', None))

    if not input_image1_url:
        print(f'[{appName}]: input_image1_url is required and is missing')
        sys.exit(1)

    if not input_image2_url:
        print(f'[{appName}]: input_image2_url is required and is missing')
        sys.exit(1)

    input['input_image1'], error = download_file(input_image1_url, 'input_image1.png')
    if error:
        print(f'[{appName}][ERROR]: Downloading image1 error: {error}')
        sys.exit(1)

    input['input_image2'], error = download_file(input_image2_url, 'input_image2.png')
    if error:
        print(f'[{appName}][ERROR]: Downloading image2 error: {error}')
        sys.exit(1)

    input_image1 = np.array(load_image(input['input_image1']))
    input_image2 = np.array(load_image(input['input_image2']))

    input_text = input.get('input_text', os.getenv('DEFAULT_INPUT_TEXT', None))
    steps = input.get('steps', int(os.getenv('DEFAULT_STEPS', '50')))
    cfg_scale = input.get('cfg_scale', float(os.getenv('DEFAULT_CFG_SCALE', '7.5')))
    eta = input.get('eta', float(os.getenv('DEFAULT_ETA', '1')))
    fps = input.get('fps', int(os.getenv('DEFAULT_FPS', '10')))
    seed = input.get('seed', int(os.getenv('DEFAULT_SEED', '42')))

    try:
        os.remove(input['input_image1'])
        os.remove(input['input_image2'])
    except:
        pass

    try:
        output_video = image2video.get_image(input_image1, input_text, steps, cfg_scale, eta, fps, seed, input_image2)

        object_name = os.path.basename(output_video)
        uploaded_url, error = upload_to_s3(output_video, bucket_name, object_name)

        if error:
            print(f'[{appName}][ERROR]: upload_to_s3 failed {error}')
            sys.exit(1)
        else:
            try:
                os.remove(output_video)
            except:
                pass

        return {'output_video_url': uploaded_url}

    except Exception as e:
        print(f'[{appName}]: ERROR image2video.get_image failed with error: {e}')
        sys.exit(1)

if __name__ == "__main__":

    sys.path.insert(1, os.path.join(sys.path[0], 'lvdm'))
    image2video = Image2Video('/tmp/', resolution='320_512')

    result, error = map_network_volume()
    if error:
        print(f'[{appName}][WARNING]: Could not map network volume: {error}')

    result, error = sync_checkpoints()
    if error:
        print(f'[{appName}][ERROR]: Failed to download checkpoints: {error}')
        sys.exit(1)

    runpod.serverless.start({'handler': handler})
