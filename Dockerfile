FROM python:3.11-slim

WORKDIR /sales_integration

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create __init__.py so 'from sales_integration.x import y' style imports work
# when PYTHONPATH=/ (service files use this style)
RUN touch __init__.py

ENV PYTHONPATH=/

CMD ["python", "manager.py"]
