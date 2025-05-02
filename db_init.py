#!/usr/bin/env python
import os
from app import create_app, db
from app.models.user import User
from app.models.satker import Satker
from app.models.asset import Asset
from app.models.asset_request import AssetRequest
from app.models.prediction import Prediction
from app.models.sbsk_validator import SBSKValidator
from datetime import datetime, timedelta
import random
import uuid

def init_db():
    """Initialize database with sample data"""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if database is already initialized
        if User.query.count() > 0:
            print("Database already initialized.")
            return
        
        print("Initializing database with sample data...")
        
        # Create satkers
        satkers = []
        for i in range(1, 6):
            satker_id = f"10508{i}"
            satker = Satker(
                satker_id=satker_id,
                satker_name=f"Satker {i}",
                employee_count=20 + (i * 10),
                address=f"Jl. Contoh No. {i}, Jakarta",
                phone=f"021-555-{1000 + i}",
                email=f"satker{i}@kemenkeu.go.id",
                eselon_id="105",
                eselon_name="Sekretariat Jenderal"
            )
            db.session.add(satker)
            satkers.append(satker)
        
        # Commit to get IDs
        db.session.commit()
        print(f"Created {len(satkers)} satkers.")
        
        # Create users
        users = []
        # Admin user
        admin = User(
            username="admin",
            email="admin@admin.com",
            password="admin123",
            satker_id=satkers[0].id,
            is_admin=True
        )
        db.session.add(admin)
        users.append(admin)
        
        # Regular users
        for i, satker in enumerate(satkers):
            user = User(
                username=f"user{i+1}",
                email=f"user{i+1}@example.com",
                password=f"password{i+1}",
                satker_id=satker.id,
                is_admin=False
            )
            db.session.add(user)
            users.append(user)
        
        # Commit to get IDs
        db.session.commit()
        print(f"Created {len(users)} users.")
        
        # Create assets
        assets = []
        # Asset codes
        asset_codes = {
            "02011": "Kendaraan Operasional",
            "02051": "Komputer PC",
            "02061": "Printer Laser",
            "02071": "Meja Kerja",
            "03111": "Gedung Kantor"
        }
        
        # Conditions
        conditions = ["Baik", "Rusak Ringan", "Rusak Berat"]
        condition_weights = [0.7, 0.2, 0.1]
        
        # Create assets for each satker
        for satker in satkers:
            # Number of assets depends on satker size
            num_assets = satker.employee_count // 2
            
            for i in range(1, num_assets + 1):
                # Select random asset code
                asset_code = random.choice(list(asset_codes.keys()))
                asset_name = asset_codes[asset_code]
                
                # Generate asset ID
                asset_id = f"BMN-{satker.satker_id}-{i:04d}"
                
                # Select condition based on weights
                condition = random.choices(conditions, condition_weights)[0]
                
                # Generate random acquisition date within last 5 years
                days_ago = random.randint(1, 5 * 365)
                acquisition_date = datetime.now() - timedelta(days=days_ago)
                
                # Generate random acquisition value based on asset type
                if asset_code.startswith("03"):  # Buildings
                    acquisition_value = random.randint(1000, 5000) * 1000000
                elif asset_code.startswith("02"):  # Equipment
                    if asset_code[2:4] == "01":  # Vehicles
                        acquisition_value = random.randint(200, 500) * 1000000
                    elif asset_code[2:4] == "05":  # Computers
                        acquisition_value = random.randint(10, 20) * 1000000
                    else:  # Other equipment
                        acquisition_value = random.randint(1, 10) * 1000000
                else:
                    acquisition_value = random.randint(1, 5) * 1000000
                
                # Create asset
                asset = Asset(
                    asset_id=asset_id,
                    asset_code=asset_code,
                    asset_name=f"{asset_name} {i}",
                    asset_condition=condition,
                    satker_id=satker.id,
                    acquisition_date=acquisition_date,
                    acquisition_value=acquisition_value,
                    location=f"Lantai {random.randint(1, 5)}, Ruang {random.randint(101, 120)}",
                    usage_status="Digunakan" if random.random() < 0.8 else "Idle"
                )
                db.session.add(asset)
                assets.append(asset)
        
        # Commit to get IDs
        db.session.commit()
        print(f"Created {len(assets)} assets.")
        
        # Create SBSK validators for common asset codes
        validators = []
        for asset_code, asset_name in asset_codes.items():
            # Create validator with custom rules
            if asset_code.startswith("03"):  # Buildings
                rules = {
                    'building_type': 'kantor',
                    'max_units': 1,
                    'standards': {
                        'height': {'min': 3, 'max': 4, 'unit': 'm'},
                        'area_per_employee': {'value': 9, 'unit': 'm²'}
                    }
                }
            elif asset_code.startswith("02"):
                if asset_code[2:4] == "01":  # Vehicles
                    rules = {
                        'vehicle_type': 'operasional',
                        'max_units': 5,
                        'standards': {
                            'replacement_age': {'value': 10, 'unit': 'tahun'},
                            'replacement_distance': {'value': 150000, 'unit': 'km'}
                        }
                    }
                elif asset_code[2:4] == "05":  # Computers
                    rules = {
                        'max_units': 1,  # 1 per employee
                        'standards': {
                            'replacement_age': {'value': 5, 'unit': 'tahun'}
                        }
                    }
                else:  # Other equipment
                    rules = {
                        'max_units': 1,  # 1 per department (10 employees)
                        'standards': {
                            'replacement_age': {'value': 5, 'unit': 'tahun'}
                        }
                    }
            else:
                rules = {
                    'max_units': 10,
                    'standards': {
                        'replacement_age': {'value': 5, 'unit': 'tahun'}
                    }
                }
            
            validator = SBSKValidator(asset_code, rules)
            db.session.add(validator)
            validators.append(validator)
        
        # Commit to get IDs
        db.session.commit()
        print(f"Created {len(validators)} SBSK validators.")
        
        # Create asset requests
        requests = []
        for i in range(20):
            # Select random user and satker
            user = random.choice(users)
            satker = user.satker
            
            # Select random asset code
            asset_code = random.choice(list(asset_codes.keys()))
            asset_name = asset_codes[asset_code]
            
            # Generate random quantity
            if asset_code.startswith("03"):  # Buildings
                quantity = random.randint(1, 3)  # Area in hundreds of m²
            elif asset_code.startswith("02"):
                if asset_code[2:4] == "01":  # Vehicles
                    quantity = random.randint(1, 3)
                elif asset_code[2:4] == "05":  # Computers
                    quantity = random.randint(5, 20)
                else:  # Other equipment
                    quantity = random.randint(1, 10)
            else:
                quantity = random.randint(1, 5)
            
            # Generate random price
            if asset_code.startswith("03"):  # Buildings
                price = quantity * 100 * 5000000  # 5 million per m²
            elif asset_code.startswith("02"):
                if asset_code[2:4] == "01":  # Vehicles
                    price = random.randint(200, 500) * 1000000
                elif asset_code[2:4] == "05":  # Computers
                    price = quantity * random.randint(10, 20) * 1000000
                else:  # Other equipment
                    price = quantity * random.randint(1, 10) * 1000000
            else:
                price = quantity * random.randint(1, 5) * 1000000
            
            # Generate random status
            status = random.choices(
                ["Draft", "Submitted", "Approved", "Rejected"],
                [0.3, 0.3, 0.2, 0.2]
            )[0]
            
            # Generate request ID
            request_id = f"REQ-{satker.satker_id}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Create request
            request = AssetRequest(
                request_id=request_id,
                satker_id=satker.id,
                user_id=user.id,
                asset_code=asset_code,
                asset_name=f"{asset_name} Baru",
                request_quantity=quantity,
                estimated_price=price,
                fiscal_year=datetime.now().year + 1,
                purpose=f"Pengadaan {asset_name} untuk kebutuhan operasional.",
                specification=f"Spesifikasi standar untuk {asset_name}",
                status=status
            )
            
            db.session.add(request)
            requests.append(request)
        
        # Commit to get IDs
        db.session.commit()
        print(f"Created {len(requests)} asset requests.")
        
        # Create predictions for submitted requests
        predictions = []
        for request in requests:
            if request.status in ["Submitted", "Approved", "Rejected"]:
                # Determine prediction result
                if request.status == "Approved":
                    result = True
                    confidence = random.uniform(0.7, 0.95)
                elif request.status == "Rejected":
                    result = False
                    confidence = random.uniform(0.75, 0.9)
                else:
                    result = random.choices([True, False], [0.6, 0.4])[0]
                    confidence = random.uniform(0.6, 0.9)
                
                # Generate details
                details = {
                    'sbsk_compliance': {
                        'met': result,
                        'description': "Usulan memenuhi SBSK" if result else "Usulan melebihi batas SBSK"
                    },
                    'existing_assets': {
                        'optimized': result,
                        'description': "Semua aset yang ada telah dioptimalkan." if result else "Terdapat aset dalam kondisi baik yang dapat dimanfaatkan."
                    },
                    'asset_condition': {
                        'description': f"Total aset: {random.randint(5, 20)}. Kondisi baik: {random.randint(3, 15)} (70%), Rusak ringan: {random.randint(1, 5)} (20%), Rusak berat: {random.randint(0, 3)} (10%)."
                    }
                }
                
                # Create prediction
                prediction = Prediction(
                    request_id=request.id,
                    prediction_result=result,
                    confidence_level=confidence,
                    details=details
                )
                
                db.session.add(prediction)
                predictions.append(prediction)
        
        # Commit final changes
        db.session.commit()
        print(f"Created {len(predictions)} predictions.")
        
        print("Database initialization complete.")

if __name__ == '__main__':
    init_db()