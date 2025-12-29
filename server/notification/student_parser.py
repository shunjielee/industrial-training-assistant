"""
Student Email Parser for parsing and managing student email lists.
"""

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class StudentEmailParser:
    """Parse and manage student email lists"""
    
    def __init__(self):
        self.students_file = Path(settings.DATA_FOLDER) / "notifications" / "student_emails.json"
        self.students_file.parent.mkdir(parents=True, exist_ok=True)
    
    def parse_email_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse email list from uploaded file (CSV or TXT)
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Dictionary with parsed student emails
        """
        try:
            # Decode file content
            try:
                text_content = file_content.decode('utf-8')
            except:
                text_content = file_content.decode('latin-1')
            
            students = []
            
            # Check file extension
            if filename.lower().endswith('.csv'):
                students = self._parse_csv(text_content)
            elif filename.lower().endswith('.txt'):
                students = self._parse_txt(text_content)
            else:
                return {
                    "success": False,
                    "error": "Unsupported file format. Please upload CSV or TXT file."
                }
            
            # Validate emails
            valid_students = []
            invalid_emails = []
            
            for student in students:
                email = student.get('email', '').strip()
                if email and self._is_valid_email(email):
                    valid_students.append(student)
                elif email:
                    invalid_emails.append(email)
            
            # Save to file
            if valid_students:
                self.save_students(valid_students)
            
            return {
                "success": True,
                "total_parsed": len(students),
                "valid_emails": len(valid_students),
                "invalid_emails": len(invalid_emails),
                "invalid_email_list": invalid_emails[:10],  # First 10 invalid emails
                "students": valid_students
            }
            
        except Exception as e:
            logger.error(f"Error parsing email file: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse CSV file"""
        students = []
        
        # Try to detect delimiter
        sniffer = csv.Sniffer()
        try:
            delimiter = sniffer.sniff(content[:1024]).delimiter
        except:
            delimiter = ','
        
        # Parse CSV
        reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
        
        for row in reader:
            # Try different column names
            email = (
                row.get('email') or 
                row.get('Email') or 
                row.get('EMAIL') or
                row.get('e-mail') or
                row.get('E-mail')
            )
            
            name = (
                row.get('name') or 
                row.get('Name') or 
                row.get('NAME') or
                row.get('student_name') or
                row.get('Student Name')
            )
            
            student_id = (
                row.get('student_id') or 
                row.get('Student ID') or 
                row.get('student_id') or
                row.get('id') or
                row.get('ID')
            )
            
            if email:
                students.append({
                    "email": email.strip(),
                    "name": name.strip() if name else "",
                    "student_id": student_id.strip() if student_id else ""
                })
        
        return students
    
    def _parse_txt(self, content: str) -> List[Dict[str, Any]]:
        """Parse TXT file (one email per line)"""
        students = []
        
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Try to extract email, name, and ID from line
            # Format: email, name, student_id (comma separated)
            # Or just email
            parts = [p.strip() for p in line.split(',')]
            
            email = parts[0] if parts else ""
            name = parts[1] if len(parts) > 1 else ""
            student_id = parts[2] if len(parts) > 2 else ""
            
            if email:
                students.append({
                    "email": email,
                    "name": name,
                    "student_id": student_id
                })
        
        return students
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def save_students(self, students: List[Dict[str, Any]]) -> bool:
        """Save student list to JSON file"""
        try:
            data = {
                "students": students,
                "last_updated": datetime.now().isoformat(),
                "total_students": len(students)
            }
            
            with open(self.students_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(students)} student emails to {self.students_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving students: {str(e)}")
            return False
    
    def load_students(self) -> List[Dict[str, Any]]:
        """Load student list from JSON file"""
        try:
            if not self.students_file.exists():
                return []
            
            with open(self.students_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get("students", [])
            
        except Exception as e:
            logger.error(f"Error loading students: {str(e)}")
            return []
    
    def get_student_count(self) -> int:
        """Get total number of students"""
        students = self.load_students()
        return len(students)
    
    def get_student_emails(self) -> List[str]:
        """Get list of student emails only"""
        students = self.load_students()
        return [s.get('email', '') for s in students if s.get('email')]

