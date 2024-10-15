import spacy
import re
from typing import List
from app.schemas import EntitySchema

class NERAnnotation:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def annotate(self, text: str, manual_annotations: List[EntitySchema]):
        """
        Annotate the text with the provided entities and their types, 
        ensuring that the same entity is recorded only once per occurrence.
        """
        final_annotations = []
        seen_annotations = set()  # Track seen entities to avoid duplicates

        # Annotate based on manual labels only
        for manual_entity in manual_annotations:
            entity = manual_entity.entity
            entity_type = manual_entity.label
            color = manual_entity.color
            bColor = manual_entity.bColor if manual_entity.bColor else "#ffffff"
            textColor = manual_entity.textColor

            # Use regex to find all occurrences of the entity in the text
            pattern = re.escape(entity)  # Escape any special characters in the entity
            matches = list(re.finditer(pattern, text, re.IGNORECASE))

            for match in matches:
                start_pos = match.start()
                end_pos = match.end()

                # Ensure that this entity occurrence is unique
                annotation_key = (entity, start_pos, end_pos)
                if annotation_key not in seen_annotations:
                    final_annotations.append({
                        "entity": entity,
                        "label": entity_type,
                        "start_pos": start_pos,
                        "end_pos": end_pos,
                        "color": color,
                        "bColor": bColor,
                        "textColor": textColor
                    })
                    seen_annotations.add(annotation_key)  # Mark as seen

        return final_annotations
