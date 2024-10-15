class BaseAnnotation:
    def annotate(self, text: str):
        """Method to be overridden by specific annotation types"""
        raise NotImplementedError("Subclasses must implement this method")

    def preprocess(self, text: str):
        """Preprocess the text (tokenization, cleaning, etc.)"""
        return text.strip()
