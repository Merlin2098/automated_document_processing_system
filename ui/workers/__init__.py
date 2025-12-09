"""
Workers module - QThread workers para procesamiento asíncrono
"""
from .pdf_splitter_worker import PdfSplitterWorker

__all__ = ['PdfSplitterWorker']