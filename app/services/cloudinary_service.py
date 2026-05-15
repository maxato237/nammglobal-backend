import cloudinary
import cloudinary.uploader


class CloudinaryService:
    @staticmethod
    def upload(file_path_or_stream, folder: str, public_id: str = None) -> dict:
        options = {"folder": folder}
        if public_id:
            options["public_id"] = public_id
        result = cloudinary.uploader.upload(file_path_or_stream, **options)
        return {
            "public_id": result.get("public_id"),
            "url": result.get("secure_url"),
        }

    @staticmethod
    def delete(public_id: str) -> bool:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"

    @staticmethod
    def get_url(public_id: str, **transform_options) -> str:
        return cloudinary.CloudinaryImage(public_id).build_url(**transform_options)
