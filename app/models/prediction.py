from datetime import datetime
import json
from app import db

class Prediction(db.Model):
    """Prediction model for RKBMN approval/rejection predictions"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('asset_requests.id'), nullable=False)
    prediction_result = db.Column(db.Boolean, nullable=True, comment="Hasil Prediksi (True=Disetujui, False=Ditolak)")
    confidence_level = db.Column(db.Float, nullable=False, default=0.0, comment="Tingkat Keyakinan (0-1)")
    details = db.Column(db.Text, nullable=True, comment="Detail Analisis dalam format JSON")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, request_id, prediction_result=None, confidence_level=0.0, details=None):
        self.request_id = request_id
        self.prediction_result = prediction_result
        self.confidence_level = confidence_level
        if details:
            self.details = json.dumps(details) if isinstance(details, dict) else details
    
    def generate_prediction(self):
        """Generate prediction based on SBSK validation and other factors"""
        # This will orchestrate various validation checks
        from app.models.sbsk_validator import SBSKValidator
        
        # Get asset request data
        asset_request = self.asset_request
        
        # Create validator
        validator = SBSKValidator(asset_request.asset_code)
        
        # Run validation
        result = validator.validate_sbsk(asset_request)
        
        # Update prediction
        self.prediction_result = result['approved']
        self.confidence_level = result['confidence']
        self.details = json.dumps(result['details'])
        db.session.commit()
        
        return self
    
    def get_recommendation(self):
        """Get recommendations based on prediction results"""
        if not self.details:
            return "Tidak ada rekomendasi tersedia."
        
        details = json.loads(self.details) if isinstance(self.details, str) else self.details
        
        if self.prediction_result:
            return "Usulan RKBMN ini kemungkinan besar akan disetujui. Silakan lanjutkan pengajuan."
        else:
            recommendations = []
            
            if 'sbsk_compliance' in details and not details['sbsk_compliance']['met']:
                item = details['sbsk_compliance']
                if 'max_allowed' in item:
                    recommendations.append(f"Kurangi jumlah usulan menjadi {item['max_allowed']} unit sesuai dengan SBSK.")
            
            if 'existing_assets' in details and not details['existing_assets']['optimized']:
                recommendations.append("Optimalkan aset yang sudah ada sebelum mengajukan pengadaan baru.")
            
            if len(recommendations) == 0:
                recommendations.append("Tinjau kembali usulan dan pastikan sesuai dengan ketentuan yang berlaku.")
            
            return "Rekomendasi:\n- " + "\n- ".join(recommendations)
    
    def explain_reasoning(self):
        """Explain the reasoning behind the prediction"""
        if not self.details:
            return "Tidak ada detail analisis tersedia."
        
        details = json.loads(self.details) if isinstance(self.details, str) else self.details
        
        explanation = []
        
        # Check SBSK compliance
        if 'sbsk_compliance' in details:
            item = details['sbsk_compliance']
            if item['met']:
                explanation.append(f"Usulan memenuhi SBSK dengan rincian: {item['description']}")
            else:
                explanation.append(f"Usulan tidak memenuhi SBSK dengan rincian: {item['description']}")
        
        # Check existing assets
        if 'existing_assets' in details:
            item = details['existing_assets']
            if item['optimized']:
                explanation.append("Aset yang sudah ada telah dioptimalkan.")
            else:
                explanation.append(f"Aset yang sudah ada belum dioptimalkan: {item['description']}")
        
        # Check condition
        if 'asset_condition' in details:
            item = details['asset_condition']
            explanation.append(f"Analisis kondisi aset: {item['description']}")
        
        return "\n".join(explanation)
    
    def __repr__(self):
        result = "Disetujui" if self.prediction_result else "Ditolak"
        confidence = f"{self.confidence_level * 100:.2f}%"
        return f'<Prediction {self.id} Result: {result} Confidence: {confidence}>'