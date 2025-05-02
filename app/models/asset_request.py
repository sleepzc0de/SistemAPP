from datetime import datetime
from app import db

class AssetRequest(db.Model):
    """Asset request model for RKBMN submissions"""
    __tablename__ = 'asset_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(50), unique=True, index=True, nullable=False, comment="ID Permintaan")
    satker_id = db.Column(db.Integer, db.ForeignKey('satkers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    asset_code = db.Column(db.String(20), nullable=False, comment="Kode Barang sesuai Kodefikasi BMN")
    asset_name = db.Column(db.String(255), nullable=False, comment="Nama Barang")
    request_quantity = db.Column(db.Integer, nullable=False, comment="Jumlah yang Diusulkan")
    estimated_price = db.Column(db.Numeric(15, 2), nullable=True, comment="Harga Perkiraan")
    fiscal_year = db.Column(db.Integer, nullable=False, comment="Tahun Anggaran")
    purpose = db.Column(db.Text, nullable=True, comment="Tujuan Pengadaan")
    specification = db.Column(db.Text, nullable=True, comment="Spesifikasi Barang")
    status = db.Column(db.String(20), default='Draft', comment="Status Permintaan (Draft/Submitted/Approved/Rejected)")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    predictions = db.relationship('Prediction', backref='asset_request', lazy='dynamic')
    
    def __init__(self, request_id, satker_id, user_id, asset_code, asset_name, request_quantity, fiscal_year, **kwargs):
        self.request_id = request_id
        self.satker_id = satker_id
        self.user_id = user_id
        self.asset_code = asset_code
        self.asset_name = asset_name
        self.request_quantity = request_quantity
        self.fiscal_year = fiscal_year
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def calculate_eligibility(self):
        """Calculate whether the request meets eligibility criteria"""
        # This will implement business logic based on SBSK and other factors
        from app.models.sbsk_validator import SBSKValidator
        
        validator = SBSKValidator(self.asset_code)
        return validator.validate_sbsk(self)
    
    def submit_for_prediction(self):
        """Submit the request for prediction"""
        from app.models.prediction import Prediction
        
        prediction = Prediction(
            request_id=self.id,
            prediction_result=None,
            confidence_level=0.0
        )
        db.session.add(prediction)
        db.session.commit()
        
        # Update prediction result
        result = self.calculate_eligibility()
        prediction.prediction_result = result['approved']
        prediction.confidence_level = result['confidence']
        prediction.details = result['details']
        db.session.commit()
        
        return prediction
    
    def get_result_message(self):
        """Get a formatted message with the prediction result"""
        latest_prediction = self.predictions.order_by(Prediction.created_at.desc()).first()
        
        if not latest_prediction:
            return "Belum ada prediksi untuk pengajuan ini."
        
        result = "Disetujui" if latest_prediction.prediction_result else "Ditolak"
        confidence = f"{latest_prediction.confidence_level * 100:.2f}%"
        
        message = f"Prediksi: {result} dengan tingkat keyakinan {confidence}\n"
        message += f"Detail analisis: {latest_prediction.details}"
        
        return message
    
    def __repr__(self):
        return f'<AssetRequest {self.request_id} {self.asset_name}>'