from typing import TypedDict, List, Optional, Dict, Any
from backend.services import llm_bio_generator

class BioGraphState(TypedDict):
    """
    Represents the state of our graph.
    
    Attributes:
        keyword: The main keyword for generation.
        website: The website of the entity.
        num_bio_entities: Optional number of bios to generate.
        address: Optional address.
        username: Optional username.
        name: Optional entity name.
        zipcode: Optional zipcode.
        hotline: Optional hotline.
        main_keyword: Optional main keyword.
        short_description: Optional short description.
        hashtag: The generated hashtags string.
        bioEntities: The list of generated bio paragraphs.
    """
    keyword: str
    website: str
    num_bio_entities: Optional[int]
    address: Optional[str]
    username: Optional[str]
    name: Optional[str]
    zipcode: Optional[str]
    hotline: Optional[str]
    main_keyword: Optional[str]
    short_description: Optional[str]
    language: Optional[str]
    entity_context: Optional[str] # Thêm trường context
    
    # Fields to be populated by the workflow
    hashtag: str
    bioEntities: List[str]


# --- Node Functions ---

async def generate_basic_info(state: BioGraphState) -> BioGraphState:
    """
    Node to generate or complete the basic information.
    Calls the async version of the service function.
    """
    # LangGraph passes the entire state dictionary to the node.
    updated_info = await llm_bio_generator.generate_basic_info(state)
    
    # Merge the updated info back into the state
    state.update(updated_info)
    return state

async def generate_hashtags(state: BioGraphState) -> BioGraphState:
    """
    Node to generate hashtags based on the completed basic info.
    """
    updated_state = await llm_bio_generator.generate_hashtags(state)
    state.update(updated_state)
    return state

async def generate_bio_entities(state: BioGraphState) -> BioGraphState:
    """
    Node to generate the final bio entities.
    """
    updated_state = await llm_bio_generator.generate_bio_entities(state)
    state.update(updated_state)
    return state
