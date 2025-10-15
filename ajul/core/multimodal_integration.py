"""
Multimodal Data Integration Module

Integrates text, images, and graph data for enhanced agent reasoning.

Key capabilities:
- Process images (charts, diagrams, papers) with Claude Vision
- Extract information from visual content
- Combine multimodal data for hypothesis generation
- Store and retrieve multimodal memories
- Graph-based knowledge representation

Inspired by Mem0 multimodal support and Claude Vision API.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import base64
import json
import os
from pathlib import Path
import hashlib

from anthropic import AsyncAnthropic
from loguru import logger


class ModalityType(str, Enum):
    """Types of data modalities"""
    TEXT = "text"
    IMAGE = "image"
    GRAPH = "graph"
    TABLE = "table"
    CHART = "chart"
    DIAGRAM = "diagram"


class ImageFormat(str, Enum):
    """Supported image formats"""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"


@dataclass
class ImageData:
    """Image data container"""
    id: str
    source: str  # URL or file path
    format: ImageFormat
    data: Optional[str] = None  # Base64 encoded
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphData:
    """Graph/network data"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultimodalInput:
    """Combined multimodal input"""
    id: str
    modalities: Dict[ModalityType, Any]
    context: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExtractedInformation:
    """Information extracted from multimodal input"""
    source_id: str
    modality: ModalityType
    extracted_text: str
    structured_data: Dict[str, Any]
    confidence: float
    entities: List[str] = field(default_factory=list)
    relationships: List[Dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MultimodalMemory:
    """Multimodal memory entry"""
    id: str
    content: str
    modalities_used: List[ModalityType]
    source_ids: List[str]
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class MultimodalIntegrationEngine:
    """
    Engine for integrating multiple data modalities.

    Workflow:
    1. Accept text, image, graph inputs
    2. Process each modality appropriately
    3. Extract structured information
    4. Combine into unified representation
    5. Store as searchable memories
    6. Enable multimodal reasoning
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        vision_model: str = "claude-sonnet-4-20250514",
        max_images_per_request: int = 20,
        max_image_size_mb: int = 5
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.vision_model = vision_model
        self.max_images_per_request = max_images_per_request
        self.max_image_size_mb = max_image_size_mb

        # Storage
        self.images: Dict[str, ImageData] = {}
        self.graphs: Dict[str, GraphData] = {}
        self.extractions: List[ExtractedInformation] = []
        self.memories: List[MultimodalMemory] = {}

        logger.info("Multimodal integration engine initialized")

    async def process_image(
        self,
        image_source: str,
        context: Optional[str] = None,
        is_url: bool = False
    ) -> ExtractedInformation:
        """
        Process image and extract information using Claude Vision.

        Args:
            image_source: URL or file path
            context: Optional context about the image
            is_url: True if image_source is URL, False if file path

        Returns:
            Extracted information
        """
        logger.info(f"Processing image: {image_source}")

        # Prepare image data
        if is_url:
            image_content = {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": image_source
                }
            }
            image_id = self._generate_id(image_source)
        else:
            # Load and encode local file
            base64_image = self._encode_image(image_source)
            image_format = self._detect_image_format(image_source)

            image_content = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": f"image/{image_format.value}",
                    "data": base64_image
                }
            }
            image_id = self._generate_id(image_source)

            # Store image data
            self.images[image_id] = ImageData(
                id=image_id,
                source=image_source,
                format=image_format,
                data=base64_image
            )

        # Build prompt
        analysis_prompt = self._build_image_analysis_prompt(context)

        # Call Claude Vision
        try:
            response = await self.client.messages.create(
                model=self.vision_model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            image_content,
                            {
                                "type": "text",
                                "text": analysis_prompt
                            }
                        ]
                    }
                ]
            )

            extracted_text = response.content[0].text

            # Parse structured data
            structured = self._parse_vision_output(extracted_text)

            extraction = ExtractedInformation(
                source_id=image_id,
                modality=ModalityType.IMAGE,
                extracted_text=extracted_text,
                structured_data=structured,
                confidence=0.85,
                entities=structured.get("entities", []),
                relationships=structured.get("relationships", [])
            )

            self.extractions.append(extraction)

            logger.success(f"Image processed: {len(extracted_text)} chars extracted")
            return extraction

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise

    async def process_multiple_images(
        self,
        image_sources: List[str],
        context: str,
        comparison: bool = False
    ) -> List[ExtractedInformation]:
        """
        Process multiple images together.

        Args:
            image_sources: List of image URLs or paths
            context: Context for all images
            comparison: If True, compare images

        Returns:
            List of extractions
        """
        logger.info(f"Processing {len(image_sources)} images")

        if len(image_sources) > self.max_images_per_request:
            logger.warning(
                f"Too many images ({len(image_sources)}), "
                f"processing first {self.max_images_per_request}"
            )
            image_sources = image_sources[:self.max_images_per_request]

        extractions = []

        if comparison:
            # Process all together for comparison
            extraction = await self._process_images_comparison(
                image_sources,
                context
            )
            extractions.append(extraction)
        else:
            # Process individually
            for source in image_sources:
                extraction = await self.process_image(source, context)
                extractions.append(extraction)

        return extractions

    async def _process_images_comparison(
        self,
        image_sources: List[str],
        context: str
    ) -> ExtractedInformation:
        """Process multiple images for comparison"""

        # Prepare image contents
        content_blocks = []

        for source in image_sources:
            if source.startswith("http"):
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": source
                    }
                })
            else:
                base64_image = self._encode_image(source)
                format = self._detect_image_format(source)
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{format.value}",
                        "data": base64_image
                    }
                })

        # Add comparison prompt
        content_blocks.append({
            "type": "text",
            "text": f"""Compare and analyze these images:

Context: {context}

Provide:
1. Common elements across images
2. Key differences
3. Patterns or trends
4. Important details from each
5. Overall insights

Be thorough and specific.
"""
        })

        response = await self.client.messages.create(
            model=self.vision_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": content_blocks}]
        )

        extracted_text = response.content[0].text

        return ExtractedInformation(
            source_id="comparison_" + self._generate_id("_".join(image_sources)),
            modality=ModalityType.IMAGE,
            extracted_text=extracted_text,
            structured_data={"comparison": True, "num_images": len(image_sources)},
            confidence=0.85
        )

    async def process_graph_data(
        self,
        graph: GraphData,
        analysis_goal: str
    ) -> ExtractedInformation:
        """
        Process graph/network data.

        Args:
            graph: Graph data structure
            analysis_goal: What to analyze

        Returns:
            Extracted insights
        """
        logger.info(f"Processing graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

        # Convert graph to textual representation
        graph_text = self._graph_to_text(graph)

        prompt = f"""Analyze this graph/network data:

{graph_text}

Analysis goal: {analysis_goal}

Provide insights:
1. Key nodes (central entities)
2. Important relationships
3. Clusters or communities
4. Patterns
5. Anomalies
6. Actionable insights

Format as structured analysis.
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=3072,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text

            graph_id = self._generate_id(json.dumps(graph.nodes))
            self.graphs[graph_id] = graph

            extraction = ExtractedInformation(
                source_id=graph_id,
                modality=ModalityType.GRAPH,
                extracted_text=analysis_text,
                structured_data={
                    "num_nodes": len(graph.nodes),
                    "num_edges": len(graph.edges)
                },
                confidence=0.9
            )

            self.extractions.append(extraction)

            logger.success("Graph analyzed")
            return extraction

        except Exception as e:
            logger.error(f"Graph processing failed: {e}")
            raise

    async def integrate_multimodal_input(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        graphs: Optional[List[GraphData]] = None,
        context: str = ""
    ) -> MultimodalInput:
        """
        Integrate multiple modalities into unified input.

        Args:
            text: Text data
            images: Image sources
            graphs: Graph data structures
            context: Overall context

        Returns:
            Integrated multimodal input
        """
        logger.info("Integrating multimodal input")

        modalities = {}
        extractions = []

        # Process text
        if text:
            modalities[ModalityType.TEXT] = text

        # Process images
        if images:
            image_extractions = await self.process_multiple_images(
                images,
                context
            )
            modalities[ModalityType.IMAGE] = image_extractions
            extractions.extend(image_extractions)

        # Process graphs
        if graphs:
            graph_extractions = []
            for graph in graphs:
                extraction = await self.process_graph_data(graph, context)
                graph_extractions.append(extraction)
            modalities[ModalityType.GRAPH] = graph_extractions
            extractions.extend(graph_extractions)

        input_id = self._generate_id(context + str(datetime.now()))

        multimodal_input = MultimodalInput(
            id=input_id,
            modalities=modalities,
            context=context
        )

        logger.success(f"Integrated {len(modalities)} modalities")
        return multimodal_input

    async def create_multimodal_memory(
        self,
        multimodal_input: MultimodalInput,
        user_id: str
    ) -> MultimodalMemory:
        """
        Create searchable memory from multimodal input.

        Args:
            multimodal_input: Integrated input
            user_id: User identifier

        Returns:
            Multimodal memory
        """
        logger.info("Creating multimodal memory")

        # Synthesize content from all modalities
        synthesis_prompt = self._build_synthesis_prompt(multimodal_input)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )

        synthesized_content = response.content[0].text

        memory = MultimodalMemory(
            id=multimodal_input.id,
            content=synthesized_content,
            modalities_used=list(multimodal_input.modalities.keys()),
            source_ids=[multimodal_input.id],
            metadata={
                "user_id": user_id,
                "context": multimodal_input.context
            }
        )

        self.memories[memory.id] = memory

        logger.success("Multimodal memory created")
        return memory

    async def query_multimodal_context(
        self,
        query: str,
        modalities: Optional[List[ModalityType]] = None
    ) -> List[ExtractedInformation]:
        """
        Query across multimodal memories.

        Args:
            query: Search query
            modalities: Filter by modality types

        Returns:
            Relevant extractions
        """
        logger.info(f"Querying multimodal context: {query}")

        # Filter extractions
        relevant = []

        for extraction in self.extractions:
            # Filter by modality if specified
            if modalities and extraction.modality not in modalities:
                continue

            # Simple relevance check (in production, use embeddings)
            if query.lower() in extraction.extracted_text.lower():
                relevant.append(extraction)

        logger.info(f"Found {len(relevant)} relevant extractions")
        return relevant

    # Helper methods

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _detect_image_format(self, image_path: str) -> ImageFormat:
        """Detect image format from file extension"""
        ext = Path(image_path).suffix.lower()
        format_map = {
            '.jpg': ImageFormat.JPEG,
            '.jpeg': ImageFormat.JPEG,
            '.png': ImageFormat.PNG,
            '.webp': ImageFormat.WEBP,
            '.gif': ImageFormat.GIF
        }
        return format_map.get(ext, ImageFormat.JPEG)

    def _build_image_analysis_prompt(self, context: Optional[str]) -> str:
        """Build prompt for image analysis"""

        base = """Analyze this image in detail and extract all relevant information.

Provide:
1. **Description**: What is shown in the image
2. **Text Content**: Any text visible (OCR)
3. **Data/Numbers**: Any numerical data, statistics, measurements
4. **Entities**: People, places, objects, concepts mentioned
5. **Relationships**: Connections between entities
6. **Insights**: Key takeaways or patterns
7. **Type**: Chart, diagram, photo, document, etc.

"""
        if context:
            base += f"\n**Context**: {context}\n"

        base += "\nBe thorough and extract all useful information."

        return base

    def _parse_vision_output(self, text: str) -> Dict[str, Any]:
        """Parse structured data from vision output"""

        # Simplified parsing
        structured = {
            "full_text": text,
            "entities": [],
            "relationships": []
        }

        # Extract entities (simplified)
        import re
        entities = re.findall(r'\*\*(.+?)\*\*', text)
        structured["entities"] = entities[:10]  # Limit

        return structured

    def _graph_to_text(self, graph: GraphData) -> str:
        """Convert graph to textual representation"""

        text = f"**Graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges**\n\n"

        text += "**Nodes**:\n"
        for node in graph.nodes[:20]:  # Limit for context
            text += f"- {node.get('id', 'unknown')}: {node.get('label', '')}\n"

        text += "\n**Edges**:\n"
        for edge in graph.edges[:30]:
            text += f"- {edge.get('source')} → {edge.get('target')}: {edge.get('label', 'connected')}\n"

        return text

    def _build_synthesis_prompt(self, multimodal_input: MultimodalInput) -> str:
        """Build prompt to synthesize multimodal content"""

        prompt = f"Synthesize information from multiple sources:\n\n"
        prompt += f"**Context**: {multimodal_input.context}\n\n"

        # Add text
        if ModalityType.TEXT in multimodal_input.modalities:
            prompt += f"**Text**:\n{multimodal_input.modalities[ModalityType.TEXT]}\n\n"

        # Add image extractions
        if ModalityType.IMAGE in multimodal_input.modalities:
            extractions = multimodal_input.modalities[ModalityType.IMAGE]
            prompt += f"**From Images** ({len(extractions)} images):\n"
            for ext in extractions:
                prompt += f"- {ext.extracted_text[:200]}...\n"
            prompt += "\n"

        # Add graph insights
        if ModalityType.GRAPH in multimodal_input.modalities:
            extractions = multimodal_input.modalities[ModalityType.GRAPH]
            prompt += f"**From Graphs**:\n"
            for ext in extractions:
                prompt += f"- {ext.extracted_text[:200]}...\n"
            prompt += "\n"

        prompt += """
Create a coherent synthesis:
1. Combine all information
2. Identify key insights
3. Note connections across modalities
4. Summarize important points

Output concise but comprehensive synthesis.
"""

        return prompt

    def _generate_id(self, text: str) -> str:
        """Generate unique ID"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of multimodal processing"""

        modality_counts = {}
        for extraction in self.extractions:
            modality = extraction.modality.value
            modality_counts[modality] = modality_counts.get(modality, 0) + 1

        return {
            "total_extractions": len(self.extractions),
            "by_modality": modality_counts,
            "images_processed": len(self.images),
            "graphs_processed": len(self.graphs),
            "memories_created": len(self.memories),
            "recent_extractions": [
                {
                    "modality": e.modality.value,
                    "confidence": e.confidence,
                    "entities_found": len(e.entities)
                }
                for e in self.extractions[-5:]
            ]
        }
