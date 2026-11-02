FROM python:3.12-slim

# Hugging Face talab qiladigan xavfsiz foydalanuvchi yaratish
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /home/user/app

COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user:user . .

EXPOSE 7860

CMD ["python", "main.py"]
