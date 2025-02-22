from celery import Celery

# Initialize Celery with Redis as the broker
celery_app = Celery("image_processing", broker="redis://localhost:6379/0")

celery_app.conf.update(
    {
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
    }
)
