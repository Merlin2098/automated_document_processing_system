"""
Tabs Package - Tabs principales de la aplicación
"""
from .tab_quick_tools import TabQuickTools
from .tab_rename_auxiliar import TabRenameAuxiliar
from .tab_pipeline_core import TabPipelineCore
from .tab_pipeline_sunat import TabPipelineSunat
from .tab_settings import TabSettings

__all__ = [
    'TabQuickTools',
    'TabRenameAuxiliar',
    'TabPipelineCore',
    'TabPipelineSunat',
    'TabSettings'
]
