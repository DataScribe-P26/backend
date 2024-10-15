from fastapi import HTTPException
from .base_annotation import BaseAnnotation
from typing import Dict,List

class ClassificationAnnotation(BaseAnnotation):
    def __init__(self):
        self.categories: Dict[str, List[str]] = {
            "technology": ["computer", "software", "hardware", "internet", "programming"],
            "sports": ["football", "basketball", "tennis", "soccer", "athlete"],
            "politics": ["government", "election", "politician", "democracy", "policy"],
        }
    
    def classify(self, text: str) -> Dict[str, float]:
        text = text.lower()
        scores = {category: 0 for category in self.categories}
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text:
                    scores[category] += 1
        
        total_score = sum(scores.values())
        if total_score == 0:
            return {"unknown": 1.0}
        
        return {category: score / total_score for category, score in scores.items()}

# for auto adding the categories 
'''

class CategoryDefinition(BaseModel):
    name: str
    keywords: List[str]

class ClassificationRequest(BaseModel):
    text: str
    categories: Optional[List[CategoryDefinition]] = None

class ClassificationAnnotation(BaseAnnotation):
    def __init__(self):
        self.default_categories: Dict[str, List[str]] = {
            "technology": ["computer", "software", "hardware", "internet", "programming"],
            "sports": ["football", "basketball", "tennis", "soccer", "athlete"],
            "politics": ["government", "election", "politician", "democracy", "policy"],
        }

    def set_categories(self, categories: List[CategoryDefinition]):
        self.categories = {category.name: category.keywords for category in categories}

    def classify(self, text: str, custom_categories: Optional[Dict[str, List[str]]] = None) -> Dict[str, float]:
        categories = custom_categories or self.default_categories
        text = text.lower()
        scores = {category: 0 for category in categories}

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    scores[category] += 1

        total_score = sum(scores.values())
        if total_score == 0:
            return {"unknown": 1.0}

        return {category: score / total_score for category, score in scores.items()}

    def annotate(self, request: ClassificationRequest) -> Dict[str, float]:
        try:
            if request.categories:
                custom_categories = {category.name: category.keywords for category in request.categories}
                return self.classify(request.text, custom_categories)
            else:
                return self.classify(request.text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

# FastAPI route
from fastapi import APIRouter

router = APIRouter()

@router.post("/annotate/classification")
async def annotate_classification(request: ClassificationRequest):
    classifier = ClassificationAnnotation()
    result = classifier.annotate(request)
    return {
        "text": request.text,
        "classification": result,
        "top_category": max(result, key=result.get),
        "confidence": max(result.values())
    }

'''