#!/usr/bin/env python3
"""
ACGI Purchased Products Export Script

This script exports purchased products from ACGI by reading customer IDs from a CSV file
and fetching purchased products data for each customer using the ECSSAWEBSVCLIB.GET_PURCHASED_PRODUCTS_XML endpoint.
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
from shared_utils import BaseExporter, validate_credentials, get_output_filename, logger
from config import ExportConfig

class PurchasedProductsExporter(BaseExporter):
    """Export purchased products from ACGI"""
    
    def get_customer_purchased_products(self, customer_id: str) -> Dict[str, Any]:
        """
        Get purchased products for a specific customer
        
        Args:
            customer_id: Customer ID to fetch purchased products for
            
        Returns:
            Dictionary containing success status and purchased products data
        """
        try:
            result = self.acgi_client.get_purchased_products(self.credentials, customer_id)
            
            if result['success']:
                purchased_products = result.get('purchased_products', {}).get('purchased_products', [])
                # Add customer ID to each product
                for product in purchased_products:
                    product['customerId'] = customer_id
                return {
                    'success': True,
                    'purchased_products': purchased_products
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error'),
                    'purchased_products': []
                }
                
        except Exception as e:
            logger.error(f"Error getting purchased products for customer {customer_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'purchased_products': []
            }
    
    def parse_purchased_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse purchased product data for CSV export
        
        Args:
            product: Purchased product data dictionary
            
        Returns:
            Parsed product data for CSV
        """
        return {
            'customerId': product.get('customerId', ''),
            'productSerno': product.get('productSerno', ''),
            'productId': product.get('productId', ''),
            'productName': product.get('productName', ''),
            'length': product.get('length', ''),
            'width': product.get('width', ''),
            'height': product.get('height', ''),
            'weight': product.get('weight', ''),
            'activeFlag': product.get('activeFlag', ''),
            'internalOrderFlag': product.get('internalOrderFlag', ''),
            'firstAvailableDate': product.get('firstAvailableDate', ''),
            'defaultUnitCost': product.get('defaultUnitCost', ''),
            'showProductRelativeURL': product.get('showProductRelativeURL', ''),
            'imageThumbnail': product.get('imageThumbnail', ''),
            'imageFullsize': product.get('imageFullsize', ''),
            'orderDate': product.get('orderDate', ''),
            'orderStatus': product.get('orderStatus', ''),
            'orderSerno': product.get('orderSerno', ''),
            'productType': product.get('productType', ''),
            'priceProfile': product.get('priceProfile', ''),
            'invoiceBalanceStatus': product.get('invoiceBalanceStatus', ''),
            'invoiceBalance': product.get('invoiceBalance', ''),
            'quantity': product.get('quantity', '')
        }
    
    def export_purchased_products_to_csv(self, csv_file_path: str, id_column: str = 'custId', output_file: str = None) -> str:
        """
        Export purchased products to CSV
        
        Args:
            csv_file_path: Path to CSV file containing customer IDs
            id_column: Name of the column containing customer IDs
            output_file: Optional output file path
            
        Returns:
            Path to the created CSV file
        """
        if output_file is None:
            output_file = get_output_filename('purchased_products')
        
        self.start_time = datetime.now()
        logger.info(f"Starting purchased products export to {output_file}")
        logger.info(f"Reading customer IDs from {csv_file_path}")
        
        # Read customer IDs from CSV
        customer_ids = self.read_customer_ids_from_csv(csv_file_path, id_column)
        
        if not customer_ids:
            logger.warning("No customer IDs found in CSV file")
            return output_file
        
        all_products = []
        
        for i, customer_id in enumerate(customer_ids, 1):
            logger.info(f"Processing customer {i}/{len(customer_ids)}: {customer_id}")
            
            # Get purchased products for this customer
            result = self.get_customer_purchased_products(customer_id)
            
            if result['success']:
                products = result['purchased_products']
                all_products.extend(products)
                self.total_exported += len(products)
                logger.info(f"  Found {len(products)} purchased products")
            else:
                self.total_errors += 1
                logger.error(f"  Error: {result.get('error', 'Unknown error')}")
            
            self.total_processed += 1
            
            # Add delay between requests
            time.sleep(ExportConfig.REQUEST_DELAY)
        
        # Parse products for CSV
        parsed_products = [self.parse_purchased_product_data(product) for product in all_products]
        
        # Define CSV columns
        fieldnames = [
            'customerId', 'productSerno', 'productId', 'productName', 'length', 'width',
            'height', 'weight', 'activeFlag', 'internalOrderFlag', 'firstAvailableDate',
            'defaultUnitCost', 'showProductRelativeURL', 'imageThumbnail', 'imageFullsize',
            'orderDate', 'orderStatus', 'orderSerno', 'productType', 'priceProfile',
            'invoiceBalanceStatus', 'invoiceBalance', 'quantity'
        ]
        
        # Write to CSV
        self.write_to_csv(parsed_products, output_file, fieldnames)
        
        # Print summary
        self.print_summary("Purchased Products")
        
        return output_file


def main():
    """Main function to run the purchased products export"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export ACGI Purchased Products to CSV')
    parser.add_argument('csv_file', help='Path to CSV file containing customer IDs')
    parser.add_argument('--id-column', default='custId', help='Name of the column containing customer IDs (default: custId)')
    parser.add_argument('--output', help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Validate credentials
    credentials = validate_credentials()
    
    # Create exporter and run export
    exporter = PurchasedProductsExporter(credentials)
    
    try:
        output_file = exporter.export_purchased_products_to_csv(
            csv_file_path=args.csv_file,
            id_column=args.id_column,
            output_file=args.output
        )
        logger.info(f"Purchased products export completed successfully: {output_file}")
    except KeyboardInterrupt:
        logger.info("Purchased products export interrupted by user")
    except Exception as e:
        logger.error(f"Purchased products export failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
