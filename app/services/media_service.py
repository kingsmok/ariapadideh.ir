"""
Media Service
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Media


class MediaService:
    """Media Upload and Processing Service"""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 'svg'}
    IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in MediaService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_file_type(mime_type: str) -> str:
        """Determine file type from MIME type"""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type in ['application/pdf']:
            return 'document'
        elif mime_type in ['application/zip', 'application/x-rar-compressed']:
            return 'archive'
        else:
            return 'other'
    
    @staticmethod
    def generate_filename(original_filename: str) -> str:
        """Generate unique filename"""
        ext = original_filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return f"{unique_name}.{ext}"
    
    @staticmethod
    def upload(file, folder: str = '', uploaded_by: int = None) -> Optional[Media]:
        """Upload and process a file"""
        
        if not file or file.filename == '':
            return None
        
        if not MediaService.allowed_file(file.filename):
            return None
        
        filename = secure_filename(MediaService.generate_filename(file.filename))
        
        # Create folder if not exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if folder:
            upload_folder = upload_folder / folder
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = upload_folder / filename
        
        # Save file
        file.save(str(filepath))
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        # Get MIME type
        mime_type = file.content_type
        
        # Create media record
        media = Media(
            filename=filename,
            original_filename=file.filename,
            path=str(filepath),
            url=f'/static/uploads/{folder}/{filename}' if folder else f'/static/uploads/{filename}',
            mime_type=mime_type,
            file_type=MediaService.get_file_type(mime_type),
            file_size=file_size,
            folder=folder,
            uploaded_by=uploaded_by
        )
        
        # Process image if applicable
        if media.file_type == 'image':
            MediaService.process_image(media, filepath)
        
        db.session.add(media)
        db.session.commit()
        
        return media
    
    @staticmethod
    def process_image(media: Media, filepath) -> None:
        """Process image - resize, optimize, create thumbnails"""
        try:
            with Image.open(filepath) as img:
                # Get dimensions
                media.width = img.width
                media.height = img.height
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnails
                thumbnail_size = current_app.config.get('IMAGE_THUMBNAIL_SIZE', (300, 300))
                medium_size = current_app.config.get('IMAGE_MEDIUM_SIZE', (600, 600))
                
                # Thumbnail
                thumb = img.copy()
                thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                thumb_filename = f"thumb_{media.filename}"
                thumb_path = filepath.parent / thumb_filename
                thumb.save(str(thumb_path), 'WEBP', quality=85, optimize=True)
                media.thumbnail_url = media.url.replace(media.filename, thumb_filename)
                
                # Medium
                medium = img.copy()
                medium.thumbnail(medium_size, Image.Resampling.LANCZOS)
                medium_filename = f"medium_{media.filename}"
                medium_path = filepath.parent / medium_filename
                medium.save(str(medium_path), 'WEBP', quality=85, optimize=True)
                media.medium_url = media.url.replace(media.filename, medium_filename)
                
                # Optimize original
                img.save(str(filepath), 'WEBP', quality=85, optimize=True)
                
                # Update file size
                media.file_size = os.path.getsize(filepath)
                
                db.session.commit()
                
        except Exception as e:
            current_app.logger.error(f"Image processing error: {e}")
    
    @staticmethod
    def save_product_image(file, product_id: int) -> str:
        """Save product image"""
        filename = secure_filename(MediaService.generate_filename(file.filename))
        
        upload_folder = current_app.config['UPLOAD_FOLDER'] / 'products' / str(product_id)
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = upload_folder / filename
        file.save(str(filepath))
        
        return filename
    
    @staticmethod
    def save_category_image(file) -> str:
        """Save category image"""
        filename = secure_filename(MediaService.generate_filename(file.filename))
        
        upload_folder = current_app.config['UPLOAD_FOLDER'] / 'categories'
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = upload_folder / filename
        file.save(str(filepath))
        
        return filename
    
    @staticmethod
    def save_category_banner(file) -> str:
        """Save category banner"""
        filename = secure_filename(MediaService.generate_filename(file.filename))
        
        upload_folder = current_app.config['UPLOAD_FOLDER'] / 'categories'
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = upload_folder / filename
        file.save(str(filepath))
        
        return filename
    
    @staticmethod
    def save_slider_image(file) -> str:
        """Save slider image"""
        filename = secure_filename(MediaService.generate_filename(file.filename))
        
        upload_folder = current_app.config['UPLOAD_FOLDER'] / 'sliders'
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = upload_folder / filename
        file.save(str(filepath))
        
        # Process slider image
        try:
            with Image.open(filepath) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(str(filepath), 'WEBP', quality=90, optimize=True)
        except Exception as e:
            current_app.logger.error(f"Slider image processing error: {e}")
        
        return filename
    
    @staticmethod
    def save_banner_image(file) -> str:
        """Save banner image"""
        filename = secure_filename(MediaService.generate_filename(file.filename))
        
        upload_folder = current_app.config['UPLOAD_FOLDER'] / 'banners'
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = upload_folder / filename
        file.save(str(filepath))
        
        return filename
    
    @staticmethod
    def save_post_image(file, post_id: int) -> str:
        """Save post image"""
        filename = secure_filename(MediaService.generate_filename(file.filename))
        
        upload_folder = current_app.config['UPLOAD_FOLDER'] / 'posts' / str(post_id)
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = upload_folder / filename
        file.save(str(filepath))
        
        return filename
    
    @staticmethod
    def delete(media: Media) -> bool:
        """Delete media file and record"""
        try:
            # Delete physical file
            if os.path.exists(media.path):
                os.remove(media.path)
            
            # Delete thumbnail
            if media.thumbnail_url:
                thumb_path = current_app.config['BASE_DIR'] / 'app' / 'static' / media.thumbnail_url.lstrip('/')
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            
            # Delete database record
            db.session.delete(media)
            db.session.commit()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Media deletion error: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def resize_image(filepath: str, width: int, height: int, output_path: str = None) -> str:
        """Resize an image"""
        if output_path is None:
            output_path = filepath
        
        try:
            with Image.open(filepath) as img:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
                resized.save(output_path)
            
            return output_path
            
        except Exception as e:
            current_app.logger.error(f"Image resize error: {e}")
            return filepath
    
    @staticmethod
    def create_webp(filepath: str, quality: int = 85) -> str:
        """Convert image to WebP format"""
        output_path = filepath.rsplit('.', 1)[0] + '.webp'
        
        try:
            with Image.open(filepath) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(output_path, 'WEBP', quality=quality, optimize=True)
            
            return output_path
            
        except Exception as e:
            current_app.logger.error(f"WebP conversion error: {e}")
            return filepath
