"""
Tabs Package - Tabs principales de la aplicación
"""
from .tab_quick_tools import TabQuickTools
from .tab_pipeline_core import TabPipelineCore
from .tab_pipeline_sunat import TabPipelineSunat
from .tab_settings import TabSettings

__all__ = [
    'TabQuickTools',
    'TabPipelineCore',
    'TabPipelineSunat',
    'TabSettings'
]