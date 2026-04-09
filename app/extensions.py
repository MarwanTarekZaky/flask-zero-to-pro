import logging

def register_extensions(app):
    configure_logging(app)
    
    
def configure_logging(app):
    logger = logging.getLogger()
    
    if not app.debug:
        handler = logging.FileHandler("error.log")
        handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
