FROM runpod/pytorch:2.2.1-py3.10-cuda12.1.1-devel-ubuntu22.04

# Install git, ninja, build-essential, and necessary OpenGL libraries
RUN apt-get update -y && add-apt-repository -y ppa:git-core/ppa && apt update -y && apt-get install -y \
    aria2   \
    git     \
    git-lfs \
    unzip   \
    ffmpeg  \
    vim     \
    && apt-get clean

# Set the working directory to /app
WORKDIR /app

# Clone the SadTalker repository
RUN git clone https://github.com/ToonCrafter/ToonCrafter.git /app

# Copy handler into the container at /app
COPY app/ /app

# Install any needed packages specified in requirements.txt for this handler.py
RUN pip install --upgrade -r /app/requirements.txt --no-cache-dir

# Expose the port Gradio will run on
EXPOSE 7860

# Set the entry point to run the Gradio app
CMD ["python", "/app/handler.py"]
