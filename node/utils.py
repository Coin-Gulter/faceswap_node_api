import uuid

def generate_unique_task_id(db_model):
    """
    Generates a unique task_id string using a UUIDv4 format.

    Returns:
        str: A unique task_id string.
    """

    while True:
        task_id = str(uuid.uuid4())

        # Check for uniqueness in the database
        if db_model.objects.filter(task_id=task_id).exists():
            continue  # Try again if already exists

        return task_id
    