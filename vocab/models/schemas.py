from pydantic import BaseModel, Field
from typing import Optional


class VocabularyEntry(BaseModel):
    id: Optional[str] = None
    term: str
    meaning: str
    part_of_speech: Optional[str] = None
    aspect_forms: Optional[dict] = None
    examples: Optional[list[dict]] = None
    usage_notes: Optional[str] = None
    authority_level: int = Field(default=3, ge=1, le=4)
    source: Optional[str] = None
    verified_by: Optional[str] = None
    verified_date: Optional[str] = None
    notes: Optional[str] = None


class VocabularySearchResult(VocabularyEntry):
    similarity_score: float = Field(..., description="Cosine similarity score (0–1, higher = closer match)")


class VocabularySearchResponse(BaseModel):
    query: str
    count: int
    results: list[VocabularySearchResult]


class AddVocabularyRequest(BaseModel):
    term: str = Field(..., description="Kapampangan word or phrase")
    meaning: str = Field(..., description="English meaning")
    part_of_speech: Optional[str] = Field(None, description="verb | noun | adjective | phrase")
    aspect_forms: Optional[dict] = Field(
        None,
        description='For verbs: {"progressive": "...", "completed": "...", "contemplated": "..."}'
    )
    examples: Optional[list[dict]] = Field(
        None,
        description='[{"kapampangan": "...", "english": "..."}]'
    )
    usage_notes: Optional[str] = None
    source: Optional[str] = Field(
        None,
        description="native_speaker | reference | inferred"
    )
    authority_level: int = Field(
        default=3,
        ge=1,
        le=4,
        description="1=native speaker verified, 2=academic, 3=community, 4=LLM inferred"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "term": "mangan",
                    "meaning": "to eat",
                    "part_of_speech": "verb",
                    "aspect_forms": {
                        "progressive": "mangan",
                        "completed": "mengan",
                        "contemplated": "mamangan"
                    },
                    "examples": [{"kapampangan": "Mangan ta na!", "english": "Let's eat!"}],
                    "source": "native_speaker",
                    "authority_level": 1,
                }
            ]
        }
    }
