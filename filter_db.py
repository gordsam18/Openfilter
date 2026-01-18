from openfilter.filter_runtime.filter import Filter, FilterConfig, Frame
import logging
import cv2
import numpy as np
import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DBFilterConfig(FilterConfig):
    debug: bool = False

def connect_to_database():
    """Create and return a database connection"""
    load_dotenv()
    
    db_host = os.getenv("host", "localhost")
    db_port = os.getenv("port", "5432")
    db_name = os.getenv("dbname", "postgres")
    db_user = os.getenv("user", "postgres")
    db_password = os.getenv("password", "")
    
    try:
        connection = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            dbname=db_name
        )
        logger.info("Database connection established successfully")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def add_text_to_image(image, text, position=(10, 30), font_scale=1.0, color=(0, 255, 0), thickness=2):
    """Add text to a numpy array image"""
    cv2.putText(
        image,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        thickness
    )
    return image

class DBFilter(Filter):
    @classmethod
    def normalize_config(self, config: DBFilterConfig):
        config = DBFilterConfig(super().normalize_config(config))
        return config

    def setup(self, config: DBFilterConfig):
        logger.info(f"DBFilter setup with config: {config}")
        
        self.last_person_count = 0
        self.connection = connect_to_database()

    def log_person_count_change(self, current_count, previous_count, frame_data, objects):
        """Log person count changes to PostgreSQL database"""
        if not self.connection:
            return
        
        try:
            if current_count == previous_count:
                return
            
            change_type = "increase" if current_count > previous_count else "decrease"
            
            sql = """
                INSERT INTO openfilter_example (current_count, notes)
                VALUES (%s, %s)
            """
            
            cursor = self.connection.cursor()
            cursor.execute(sql, (
                current_count,
                f"Person count {change_type}d from {previous_count} to {current_count}"
            ))
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Logged person count {change_type}: {previous_count} -> {current_count}")
            
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
            self.connection = connect_to_database()

    def process(self, frames: dict[str, Frame]):
        frame = frames.get('main')
        image = frame.rw_rgb.image
        objects = frame.data.get('objects', [])
        
        if objects:
            class_counts = {}
            for obj in objects:
                class_name = obj['class']
                confidence = obj['confidence']
                
                if class_name == 'person' and confidence <= 0.7:
                    continue
                
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            current_person_count = class_counts.get('person', 0)
            if current_person_count != self.last_person_count:
                self.log_person_count_change(current_person_count, self.last_person_count, frame.data, objects)
                self.last_person_count = current_person_count
            
            text = f"Objects: {len(objects)}"
            for class_name, count in class_counts.items():
                text += f" | {class_name}: {count}"
        else:
            text = "No objects detected"
        
        updated_image = add_text_to_image(
            image, 
            text,
            position=(10, 30),
            font_scale=0.7,
            color=(0, 255, 0),
            thickness=2
        )

        frames["main"] = Frame(
            updated_image,
            {**frame.data},
            format="RGB"
        )
        
        return frames

if __name__ == "__main__":
    DBFilter.run()
    