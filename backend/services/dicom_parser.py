import pydicom
import io

class DICOMParser:
    def extract_metadata(self, scan_bytes: bytes) -> dict:
        """
        Parses uploaded `.dcm` files directly using pydicom to extract clinical metadata.
        Returns a dictionary or None if the file is not a valid DICOM.
        """
        try:
            # We attempt to load the file as a DICOM object.
            # Usually DICOM files start with a valid preamble then 'DICM'. Pydicom handles memory streams:
            dicom_data = pydicom.dcmread(io.BytesIO(scan_bytes), force=True)
            
            # Safe extraction of metadata (some fields might be missing in anonymized or simulated files)
            patient_age = getattr(dicom_data, 'PatientAge', 'Unknown')
            modality = getattr(dicom_data, 'Modality', 'Unknown')
            slice_thickness = getattr(dicom_data, 'SliceThickness', 'Unknown')
            if slice_thickness != 'Unknown':
                slice_thickness = f"{slice_thickness} mm"
                
            return {
                "patient_age": patient_age,
                "modality": modality,
                "slice_thickness": slice_thickness,
                "dicom_valid": True
            }
        except Exception as e:
            # If not a valid DICOM, we fall back to generic inference properties
            return {
                "patient_age": "Not Available",
                "modality": "Standard Upload Protocol",
                "slice_thickness": "N/A",
                "dicom_valid": False,
                "error": str(e)
            }

dicom_parser = DICOMParser()
