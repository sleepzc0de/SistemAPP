from datetime import datetime
from app import db

class Satker(db.Model):
    """Satuan Kerja (Work Unit) model"""
    __tablename__ = 'satkers'
    
    id = db.Column(db.Integer, primary_key=True)
    satker_id = db.Column(db.String(20), unique=True, index=True, nullable=False, comment="Kode Satker dari Kemenkeu")
    satker_name = db.Column(db.String(255), nullable=False, comment="Nama Satuan Kerja")
    employee_count = db.Column(db.Integer, nullable=False, default=0, comment="Jumlah Pegawai")
    address = db.Column(db.Text, nullable=True, comment="Alamat Satker")
    phone = db.Column(db.String(20), nullable=True, comment="Nomor Telepon")
    email = db.Column(db.String(120), nullable=True, comment="Email Satker")
    eselon_id = db.Column(db.String(20), nullable=True, comment="Kode Eselon I")
    eselon_name = db.Column(db.String(255), nullable=True, comment="Nama Eselon I")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assets = db.relationship('Asset', backref='satker', lazy='dynamic')
    asset_requests = db.relationship('AssetRequest', backref='satker', lazy='dynamic')
    
    def __init__(self, satker_id, satker_name, employee_count, **kwargs):
        self.satker_id = satker_id
        self.satker_name = satker_name
        self.employee_count = employee_count
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_employee_count(self):
        """Return the current employee count"""
        return self.employee_count
    
    def update_employee_count(self, count):
        """Update employee count"""
        self.employee_count = count
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_existing_assets(self, asset_code=None):
        """Get existing assets for the satker, optionally filtered by asset code"""
        from app.models.asset import Asset
        
        query = Asset.query.filter_by(satker_id=self.id)
        if asset_code:
            query = query.filter_by(asset_code=asset_code)
        
        return query.all()
    
    def get_satker_profile(self):
        """Return a dictionary with satker profile data"""
        return {
            'id': self.id,
            'satker_id': self.satker_id,
            'satker_name': self.satker_name,
            'employee_count': self.employee_count,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'eselon_id': self.eselon_id,
            'eselon_name': self.eselon_name
        }
    
    def __repr__(self):
        return f'<Satker {self.satker_id} {self.satker_name}>'