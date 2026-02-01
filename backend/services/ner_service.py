"""
DisasterAI Backend - NER Service
Named Entity Recognition for extracting locations, organizations, and other entities
"""

import re
from typing import List, Optional, Set
from ..models import ExtractedEntity, EntityLabel, NERResult
import time


class NERService:
    """
    Named Entity Recognition service.
    Uses pattern matching and optional SpaCy for entity extraction.
    """
    
    def __init__(self, use_spacy: bool = False):
        self.use_spacy = use_spacy
        self.nlp = None
        
        if use_spacy:
            self._load_spacy()
        
        # Pattern-based extraction rules
        self._compile_patterns()
    
    def _load_spacy(self) -> None:
        """Load SpaCy model for NER"""
        try:
            import spacy
            # Try to load the model, download if not available
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Downloading SpaCy model...")
                from spacy.cli import download
                download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
        except ImportError:
            print("SpaCy not available, using pattern-based extraction only")
            self.use_spacy = False
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for entity extraction"""
        
        # Location patterns (cities, states, countries, infrastructure)
        self.location_patterns = [
            # Indian cities
            r'\b(Chennai|Bangalore|Bengaluru|Mumbai|Delhi|Kolkata|Hyderabad|Pune|Ahmedabad|Jaipur|Lucknow|Kochi|Bhubaneswar|Vishakhapatnam|Guwahati|Thiruvananthapuram|Coimbatore|Madurai|Nagpur|Indore|Patna|Ranchi|Chandigarh|Surat|Vadodara)\b',
            # Generic location patterns
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Terminal|Hub|Node|Station|Port|Airport|Center|Centre|Zone|District|Sector|Area|Region|Base|Facility|Complex|Campus)\b',
            # Explicit location mentions
            r'(?:located\s+(?:in|at|near)|based\s+in|headquarters\s+(?:in|at)|offices?\s+(?:in|at))\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        # Organization patterns
        self.org_patterns = [
            r'\b([A-Z][A-Za-z]*(?:Corp|Inc|Ltd|LLC|Pvt|Limited|Corporation|Company|Industries|Group|Foundation|Trust|Agency|Authority|Commission|Department|Ministry|Board))\b',
            r'\b([A-Z][A-Z]{2,})\b',  # Acronyms
            r'\b([A-Z][a-z]+\s+(?:Corp|Inc|Ltd|LLC|Industries|Group|Agency)\.?)\b',
        ]
        
        # Damage/Risk patterns
        self.damage_patterns = [
            r'\b(structural\s+(?:damage|failure|collapse))\b',
            r'\b((?:critical|severe|major|minor)\s+(?:damage|failure|breach|leak|disruption))\b',
            r'\b(flood(?:ing)?|earthquake|tsunami|cyclone|hurricane|tornado|wildfire|drought)\b',
            r'\b(thermal\s+(?:deviation|anomaly|variance))\b',
            r'\b(infrastructure\s+(?:failure|damage|collapse))\b',
            r'\b(power\s+(?:outage|failure|disruption))\b',
            r'\b(communication\s+(?:breakdown|failure|disruption))\b',
        ]
        
        # Urgency patterns
        self.urgency_patterns = [
            r'\b(CRITICAL|URGENT|IMMEDIATE|EMERGENCY|HIGH\s+PRIORITY|CODE\s+RED)\b',
            r'\b((?:requires?|needs?)\s+immediate\s+(?:attention|action|response))\b',
            r'\b(evacuat(?:e|ion)|rescue|emergency\s+response)\b',
        ]
        
        # Technical term patterns
        self.tech_patterns = [
            r'\b([A-Z]+[-_]?(?:[A-Z]+|\d+)+)\b',  # Technical codes
            r'\b((?:satellite|radar|sensor|thermal|infrared|GPS|GIS|IoT)\s+(?:data|imagery|analysis|monitoring|detection))\b',
            r'\b(AI|ML|deep\s+learning|neural\s+network|machine\s+learning)\b',
        ]
    
    def _extract_by_patterns(
        self, 
        text: str, 
        patterns: List[str], 
        label: EntityLabel
    ) -> List[ExtractedEntity]:
        """Extract entities matching patterns"""
        entities = []
        seen: Set[str] = set()
        
        for pattern in patterns:
            try:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Get the first capturing group or full match
                    entity_text = match.group(1) if match.groups() else match.group(0)
                    entity_text = entity_text.strip()
                    
                    # Skip if already seen or too short
                    if entity_text.lower() in seen or len(entity_text) < 2:
                        continue
                    
                    seen.add(entity_text.lower())
                    entities.append(ExtractedEntity(
                        text=entity_text,
                        label=label,
                        start_char=match.start(),
                        end_char=match.end(),
                        confidence=0.8
                    ))
            except re.error:
                continue
        
        return entities
    
    def _extract_with_spacy(self, text: str) -> List[ExtractedEntity]:
        """Extract entities using SpaCy"""
        if not self.nlp:
            return []
        
        entities = []
        doc = self.nlp(text)
        
        # Map SpaCy labels to our labels
        label_map = {
            "GPE": EntityLabel.LOCATION,
            "LOC": EntityLabel.LOCATION,
            "FAC": EntityLabel.LOCATION,
            "ORG": EntityLabel.ORGANIZATION,
            "PERSON": EntityLabel.PERSON,
            "DATE": EntityLabel.DATE,
            "TIME": EntityLabel.DATE,
            "EVENT": EntityLabel.EVENT,
        }
        
        seen: Set[str] = set()
        
        for ent in doc.ents:
            if ent.label_ not in label_map:
                continue
            
            entity_text = ent.text.strip()
            if entity_text.lower() in seen or len(entity_text) < 2:
                continue
            
            seen.add(entity_text.lower())
            entities.append(ExtractedEntity(
                text=entity_text,
                label=label_map[ent.label_],
                start_char=ent.start_char,
                end_char=ent.end_char,
                confidence=0.9
            ))
        
        return entities
    
    def extract_entities(
        self,
        text: str,
        labels: Optional[List[EntityLabel]] = None
    ) -> NERResult:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
            labels: Optional filter for specific entity types
            
        Returns:
            NERResult with extracted entities
        """
        start_time = time.time()
        all_entities: List[ExtractedEntity] = []
        
        # SpaCy extraction
        if self.use_spacy and self.nlp:
            all_entities.extend(self._extract_with_spacy(text))
        
        # Pattern-based extraction
        pattern_configs = [
            (self.location_patterns, EntityLabel.LOCATION),
            (self.org_patterns, EntityLabel.ORGANIZATION),
            (self.damage_patterns, EntityLabel.DAMAGE_TYPE),
            (self.urgency_patterns, EntityLabel.URGENCY),
            (self.tech_patterns, EntityLabel.TECH),
        ]
        
        for patterns, label in pattern_configs:
            all_entities.extend(self._extract_by_patterns(text, patterns, label))
        
        # Remove duplicates (prefer higher confidence)
        seen: dict = {}
        unique_entities = []
        
        for ent in sorted(all_entities, key=lambda x: x.confidence or 0, reverse=True):
            key = ent.text.lower()
            if key not in seen:
                seen[key] = True
                unique_entities.append(ent)
        
        # Filter by labels if specified
        if labels:
            unique_entities = [e for e in unique_entities if e.label in labels]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return NERResult(
            entities=unique_entities,
            text_length=len(text),
            processing_time_ms=processing_time
        )
    
    def extract_locations(self, text: str) -> List[str]:
        """
        Extract just location names from text.
        Convenience method for geocoding pipeline.
        
        Args:
            text: Text to extract locations from
            
        Returns:
            List of location name strings
        """
        result = self.extract_entities(text, labels=[EntityLabel.LOCATION])
        return [e.text for e in result.entities]


# Singleton instance
_service: Optional[NERService] = None


def get_ner_service(use_spacy: bool = False) -> NERService:
    """Get or create NER service instance"""
    global _service
    if _service is None:
        _service = NERService(use_spacy=use_spacy)
    return _service
