import requests
import json
from datetime import datetime
from flask import current_app
from app import db
from app.models.asset import Asset
from app.models.satker import Satker

class ExternalService:
    """Service for integrating with external systems (SIMAN, SAKTI)"""
    
    def __init__(self):
        """Initialize the service with API credentials"""
        self.siman_api_url = current_app.config.get('SIMAN_API_URL')
        self.siman_api_key = current_app.config.get('SIMAN_API_KEY')
        self.sakti_api_url = current_app.config.get('SAKTI_API_URL')
        self.sakti_api_key = current_app.config.get('SAKTI_API_KEY')
    
    def sync_assets_from_siman(self, satker_id):
        """
        Synchronize assets from SIMAN for a specific satker
        
        Args:
            satker_id: ID of the satker to sync assets for
            
        Returns:
            Dictionary with sync results
        """
        try:
            # Get satker
            satker = Satker.query.get(satker_id)
            if not satker:
                return {
                    'success': False,
                    'message': f'Satker with ID {satker_id} not found.',
                    'count': 0
                }
            
            # In a real implementation, this would make an API call to SIMAN
            # For demo purposes, we'll simulate the API response
            
            # Simulate API call
            assets_data = self._simulate_siman_assets_api(satker.satker_id)
            
            # Process assets
            count = 0
            for asset_data in assets_data:
                # Check if asset already exists
                existing_asset = Asset.query.filter_by(asset_id=asset_data['asset_id']).first()
                
                if existing_asset:
                    # Update existing asset
                    existing_asset.asset_code = asset_data['asset_code']
                    existing_asset.asset_name = asset_data['asset_name']
                    existing_asset.asset_condition = asset_data['asset_condition']
                    existing_asset.acquisition_date = datetime.strptime(asset_data['acquisition_date'], '%Y-%m-%d') if asset_data['acquisition_date'] else None
                    existing_asset.acquisition_value = asset_data['acquisition_value']
                    existing_asset.location = asset_data['location']
                    existing_asset.usage_status = asset_data['usage_status']
                else:
                    # Create new asset
                    new_asset = Asset(
                        asset_id=asset_data['asset_id'],
                        asset_code=asset_data['asset_code'],
                        asset_name=asset_data['asset_name'],
                        asset_condition=asset_data['asset_condition'],
                        satker_id=satker_id,
                        acquisition_date=datetime.strptime(asset_data['acquisition_date'], '%Y-%m-%d') if asset_data['acquisition_date'] else None,
                        acquisition_value=asset_data['acquisition_value'],
                        location=asset_data['location'],
                        usage_status=asset_data['usage_status']
                    )
                    db.session.add(new_asset)
                
                count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully synced {count} assets from SIMAN.',
                'count': count
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error syncing assets from SIMAN: {str(e)}',
                'count': 0
            }
    
    def sync_assets_from_sakti(self, satker_id):
        """
        Synchronize assets from SAKTI for a specific satker
        
        Args:
            satker_id: ID of the satker to sync assets for
            
        Returns:
            Dictionary with sync results
        """
        try:
            # Get satker
            satker = Satker.query.get(satker_id)
            if not satker:
                return {
                    'success': False,
                    'message': f'Satker with ID {satker_id} not found.',
                    'count': 0
                }
            
            # In a real implementation, this would make an API call to SAKTI
            # For demo purposes, we'll simulate the API response
            
            # Simulate API call
            assets_data = self._simulate_sakti_assets_api(satker.satker_id)
            
            # Process assets
            count = 0
            for asset_data in assets_data:
                # Check if asset already exists
                existing_asset = Asset.query.filter_by(asset_id=asset_data['asset_id']).first()
                
                if existing_asset:
                    # Update existing asset
                    existing_asset.asset_code = asset_data['asset_code']
                    existing_asset.asset_name = asset_data['asset_name']
                    existing_asset.asset_condition = asset_data['asset_condition']
                    existing_asset.acquisition_date = datetime.strptime(asset_data['acquisition_date'], '%Y-%m-%d') if asset_data['acquisition_date'] else None
                    existing_asset.acquisition_value = asset_data['acquisition_value']
                    existing_asset.location = asset_data['location']
                    existing_asset.usage_status = asset_data['usage_status']
                else:
                    # Create new asset
                    new_asset = Asset(
                        asset_id=asset_data['asset_id'],
                        asset_code=asset_data['asset_code'],
                        asset_name=asset_data['asset_name'],
                        asset_condition=asset_data['asset_condition'],
                        satker_id=satker_id,
                        acquisition_date=datetime.strptime(asset_data['acquisition_date'], '%Y-%m-%d') if asset_data['acquisition_date'] else None,
                        acquisition_value=asset_data['acquisition_value'],
                        location=asset_data['location'],
                        usage_status=asset_data['usage_status']
                    )
                    db.session.add(new_asset)
                
                count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully synced {count} assets from SAKTI.',
                'count': count
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error syncing assets from SAKTI: {str(e)}',
                'count': 0
            }
    
    def get_satker_details(self, satker_code):
        """
        Get satker details from SIMAN
        
        Args:
            satker_code: Code of the satker to get details for
            
        Returns:
            Dictionary with satker details
        """
        try:
            # In a real implementation, this would make an API call to SIMAN
            # For demo purposes, we'll simulate the API response
            
            # Simulate API call
            satker_data = self._simulate_siman_satker_api(satker_code)
            
            return {
                'success': True,
                'data': satker_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting satker details from SIMAN: {str(e)}',
                'data': None
            }
    
    def _simulate_siman_assets_api(self, satker_code):
        """
        Simulate SIMAN assets API response for demo purposes
        
        Args:
            satker_code: Code of the satker
            
        Returns:
            List of asset dictionaries
        """
        # Generate some fake assets based on satker code
        assets = []
        
        # Use last 3 digits of satker code to determine number of assets
        num_assets = int(satker_code[-3:]) % 20 + 5
        
        for i in range(1, num_assets + 1):
            asset_id = f"SIMAN-{satker_code}-{i:04d}"
            
            # Determine asset type based on index
            if i % 5 == 0:
                # Buildings
                asset_code = "03111"
                asset_name = f"Gedung Kantor Type {chr(65 + (i % 3))}"
                acquisition_value = 2500000000 + (i * 10000000)
            elif i % 4 == 0:
                # Vehicles
                asset_code = "02011"
                asset_name = f"Kendaraan Operasional {chr(65 + (i % 3))}"
                acquisition_value = 300000000 + (i * 5000000)
            elif i % 3 == 0:
                # IT Equipment
                asset_code = "02051"
                asset_name = f"Komputer PC {chr(65 + (i % 3))}"
                acquisition_value = 15000000 + (i * 1000000)
            elif i % 2 == 0:
                # Furniture
                asset_code = "02071"
                asset_name = f"Meja Kerja Type {chr(65 + (i % 3))}"
                acquisition_value = 2000000 + (i * 500000)
            else:
                # Office Equipment
                asset_code = "02061"
                asset_name = f"Printer Laser {chr(65 + (i % 3))}"
                acquisition_value = 5000000 + (i * 1000000)
            
            # Determine condition based on index
            if i % 10 < 7:
                condition = "Baik"
            elif i % 10 < 9:
                condition = "Rusak Ringan"
            else:
                condition = "Rusak Berat"
            
            # Create asset data
            asset = {
                "asset_id": asset_id,
                "asset_code": asset_code,
                "asset_name": asset_name,
                "asset_condition": condition,
                "acquisition_date": f"2020-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                "acquisition_value": acquisition_value,
                "location": f"Lantai {(i % 5) + 1}, Ruang {(i % 10) + 101}",
                "usage_status": "Digunakan" if i % 8 < 7 else "Idle"
            }
            
            assets.append(asset)
        
        return assets
    
    def _simulate_sakti_assets_api(self, satker_code):
        """
        Simulate SAKTI assets API response for demo purposes
        
        Args:
            satker_code: Code of the satker
            
        Returns:
            List of asset dictionaries
        """
        # For demo, we'll return similar data as SIMAN but with SAKTI prefix
        assets = self._simulate_siman_assets_api(satker_code)
        
        for asset in assets:
            asset['asset_id'] = asset['asset_id'].replace('SIMAN', 'SAKTI')
        
        return assets
    
    def _simulate_siman_satker_api(self, satker_code):
        """
        Simulate SIMAN satker API response for demo purposes
        
        Args:
            satker_code: Code of the satker
            
        Returns:
            Dictionary with satker details
        """
        # Generate fake satker details
        satker_data = {
            "satker_id": satker_code,
            "satker_name": f"Satker {satker_code}",
            "employee_count": int(satker_code[-3:]) % 100 + 20,
            "address": f"Jl. Contoh No. {int(satker_code[-3:]) % 100 + 1}, Jakarta",
            "phone": f"021-{satker_code[-4:]}-{satker_code[-3:]}",
            "email": f"satker{satker_code}@kemenkeu.go.id",
            "eselon_id": satker_code[:2],
            "eselon_name": f"Direktorat Jenderal {chr(65 + (int(satker_code[:2]) % 26))}"
        }
        
        return satker_data