"""Cloudinary utilities for file uploads"""
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

# Cloudinary imports (optional, will be imported if available)
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    logger.warning("cloudinary not installed. Media uploads will not work.")


# Initialize Cloudinary (singleton pattern)
_cloudinary_initialized = False


def initialize_cloudinary():
    """Initialize Cloudinary configuration"""
    global _cloudinary_initialized

    if _cloudinary_initialized:
        return True

    if not CLOUDINARY_AVAILABLE:
        logger.error("Cloudinary not installed. Run: pip install cloudinary")
        return False

    if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
        logger.warning("Cloudinary credentials not configured. Media uploads disabled.")
        return False

    try:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        _cloudinary_initialized = True
        logger.info("Cloudinary initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Cloudinary: {str(e)}")
        return False


def upload_file(file, folder="task_media", resource_type="auto"):
    """
    Upload file to Cloudinary

    Args:
        file: File object (Django UploadedFile)
        folder: Cloudinary folder name (default: "task_media")
        resource_type: "auto", "image", "video", "raw" (default: "auto")

    Returns:
        dict: {
            'url': 'https://res.cloudinary.com/...',
            'public_id': 'task_media/abc123',
            'format': 'jpg',
            'resource_type': 'image',
            'bytes': 123456
        } or None if upload fails
    """
    if not CLOUDINARY_AVAILABLE:
        logger.error("Cloudinary not available")
        return None

    if not initialize_cloudinary():
        return None

    try:
        # Upload file to Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type=resource_type,
            overwrite=False,
            unique_filename=True,
            use_filename=True
        )

        logger.info(f"File uploaded successfully: {result['public_id']}")

        return {
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'format': result.get('format', ''),
            'resource_type': result.get('resource_type', 'image'),
            'bytes': result.get('bytes', 0),
            'width': result.get('width', 0),
            'height': result.get('height', 0),
        }

    except Exception as e:
        logger.error(f"Failed to upload file to Cloudinary: {str(e)}")
        return None


def delete_file(public_id, resource_type="image"):
    """
    Delete file from Cloudinary

    Args:
        public_id: Cloudinary public ID (e.g., "task_media/abc123")
        resource_type: "image", "video", "raw" (default: "image")

    Returns:
        bool: True if deleted successfully
    """
    if not CLOUDINARY_AVAILABLE:
        logger.error("Cloudinary not available")
        return False

    if not initialize_cloudinary():
        return False

    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        logger.info(f"File deleted successfully: {public_id}")
        return result.get('result') == 'ok'

    except Exception as e:
        logger.error(f"Failed to delete file from Cloudinary: {str(e)}")
        return False


def get_file_type_from_url(url):
    """
    Determine file type from Cloudinary URL

    Args:
        url: Cloudinary URL

    Returns:
        str: "image", "video", "document", "unknown"
    """
    if not url:
        return "unknown"

    # Extract file extension from URL
    extension = os.path.splitext(url.lower())[1]

    # Image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico']
    if extension in image_extensions or '/image/' in url:
        return "image"

    # Video extensions
    video_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mkv']
    if extension in video_extensions or '/video/' in url:
        return "video"

    # Document extensions
    document_extensions = ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx']
    if extension in document_extensions:
        return "document"

    return "unknown"


def get_optimized_url(url, width=None, height=None, quality="auto"):
    """
    Get optimized Cloudinary URL with transformations

    Args:
        url: Original Cloudinary URL
        width: Target width in pixels
        height: Target height in pixels
        quality: Image quality ("auto", "best", "good", "eco", "low" or number 1-100)

    Returns:
        str: Optimized URL with transformations
    """
    if not url or 'cloudinary.com' not in url:
        return url

    # Build transformation string
    transformations = []

    if width:
        transformations.append(f"w_{width}")

    if height:
        transformations.append(f"h_{height}")

    if quality:
        transformations.append(f"q_{quality}")

    if not transformations:
        return url

    # Insert transformations into URL
    # Format: https://res.cloudinary.com/cloud_name/image/upload/TRANSFORMATIONS/...
    parts = url.split('/upload/')
    if len(parts) == 2:
        transformation_string = ','.join(transformations)
        return f"{parts[0]}/upload/{transformation_string}/{parts[1]}"

    return url
