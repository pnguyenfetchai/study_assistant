from uagents import Protocol, Model

class ImageResponse(Model):
    request: str  # Original request that generated this image
    image_data: str  # Base64 encoded image
    image_type: str  # e.g., 'png', 'jpeg'
    content_type: str  # e.g., 'image/png', 'image/jpeg'

visualization_protocol = Protocol("Visualization")

# Export the protocol and models
__all__ = ["visualization_protocol", "ImageResponse"]
