import openai
import google.generativeai as genai
from typing import List, Dict, Any
import logging
import re
from ..config import settings
from groq import Groq

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: str = None, use_google: bool = False, use_groq: bool = False):
        self.use_google = use_google
        self.use_groq = use_groq
        self.groq_client = None
        self.google_api_key = None
        self.api_key = None

        if use_groq:
            groq_key = api_key or settings.GROQ_API_KEY
            if groq_key:
                self.groq_client = Groq(api_key=groq_key)
        elif use_google:
            self.google_api_key = api_key or settings.GOOGLE_API_KEY
            if self.google_api_key:
                genai.configure(api_key=self.google_api_key)
                self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.api_key = api_key or settings.OPENAI_API_KEY
            if self.api_key:
                openai.api_key = self.api_key
    
    def generate_response(self, query: str, context: str, language: str = "en") -> Dict[str, Any]:
        """Generate response using Groq, Google AI, OpenAI, or fallback"""
        if self.use_groq and self.groq_client:
            return self._generate_groq_response(query, context, language)
        if self.use_google and self.google_api_key:
            return self._generate_google_response(query, context, language)
        if self.api_key:
            return self._generate_openai_response(query, context, language)
        # Fallback to simple response based on context
        return self._generate_simple_response(query, context, language)

    def _build_system_prompt(self) -> str:
        prompt = """You are an Industrial Training assistant for IT students.

You must answer ONLY using the information in the provided context from official documents.

Style:
- Use clear, natural English, like a helpful lecturer talking to a student.
- Give short answers (typically 1–4 sentences).
- Focus on the exact question: answer it directly before adding any extra details.
- You may paraphrase the document so the wording sounds natural, but the facts must stay the same.

Content rules:
- Use ONLY information that is clearly stated in the context.
- If the context contains relevant information but not the exact answer, try to infer a reasonable answer based on the available context.
- If the context does NOT clearly state a date, number, deadline, or requirement, say that the document does not specify it.
- Do NOT guess or invent new rules, dates, or requirements that are not supported by the context.
- If the question cannot be answered from the context, politely say that the documents do not provide that information.
- When answering, extract and present all relevant information from the context that relates to the question."""
        return prompt

    def _format_numbered(self, text: str) -> str:
        """Normalize numbered answers to simple comma-separated phrases (no leading numbers)."""
        if not text:
            return text
        # Split on patterns like "1)" or "1." and drop the numbers.
        parts = re.split(r'\s*\d+[\)\.]\s*', text.strip())
        items = [re.sub(r'\s+', ' ', p).strip() for p in parts if p.strip()]
        if len(items) >= 2:
            return ', '.join(items)
        return text.strip()

    def _generate_groq_response(self, query: str, context: str, language: str = "en") -> Dict[str, Any]:
        try:
            system_prompt = self._build_system_prompt()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
            model_name = settings.GROQ_MODEL or "llama-3.3-70b-versatile"
            completion = self.groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=500
            )
            response_text = completion.choices[0].message.content.strip()
            response_text = self._format_numbered(response_text)
            confidence = self._calculate_confidence(response_text, context)
            return {"response": response_text, "confidence": confidence, "model": model_name}
        except Exception as e:
            logger.error(f"Groq error: {str(e)}")
            return {"response": f"Sorry, I encountered an error: {str(e)}", "confidence": 0.0, "error": str(e)}
    
    def _generate_google_response(self, query: str, context: str, language: str = "en") -> Dict[str, Any]:
        """Generate response using Google AI"""
        try:
            system_prompt = self._build_system_prompt()
            
            # Prepare the prompt
            prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            
            # Generate response
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            response_text = self._format_numbered(response_text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(response_text, context)
            
            return {
                'response': response_text,
                'confidence': confidence,
                'model': 'gemini-pro'
            }
            
        except Exception as e:
            logger.error(f"Google AI error: {str(e)}")
            return {
                'response': f'Sorry, I encountered an error: {str(e)}',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _generate_openai_response(self, query: str, context: str, language: str = "en") -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        try:
            system_prompt = self._build_system_prompt()
            
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.5
            )
            
            response_text = response.choices[0].message.content.strip()
            response_text = self._format_numbered(response_text)
            
            # Calculate confidence based on response length and content
            confidence = self._calculate_confidence(response_text, context)
            
            return {
                'response': response_text,
                'confidence': confidence,
                'model': 'gpt-3.5-turbo'
            }
            
        except Exception as e:
            logger.error(f"LLM API error: {str(e)}")
            return {
                'response': f'Sorry, I encountered an error: {str(e)}',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _calculate_confidence(self, response: str, context: str) -> float:
        """Calculate confidence score for the response"""
        if not response or not context:
            return 0.0
        
        # Simple confidence calculation
        # Higher confidence if response is substantial and context was provided
        response_length = len(response)
        context_length = len(context)
        
        # Base confidence on response quality indicators
        confidence = 0.5  # Base confidence
        
        # Increase confidence for longer, more detailed responses
        if response_length > 100:
            confidence += 0.2
        if response_length > 200:
            confidence += 0.1
        
        # Increase confidence if context was substantial
        if context_length > 500:
            confidence += 0.2
        
        # Check for uncertainty indicators
        uncertainty_words = ['might', 'possibly', 'unclear', 'not sure', 'uncertain', 'may', 'could be']
        if any(word in response.lower() for word in uncertainty_words):
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _generate_simple_response(self, query: str, context: str, language: str = "en") -> Dict[str, Any]:
        """Generate simple response without OpenAI API"""
        if not context:
            return {
                'response': 'I could not find relevant information in the documents.',
                'confidence': 0.0,
                'model': 'local_fallback'
            }
        
        # Clean and process context
        context_clean = context.replace('\n\n', '\n').strip()
        
        # Split into paragraphs and sentences
        paragraphs = [p.strip() for p in context_clean.split('\n') if p.strip()]
        
        # Find most relevant content based on query keywords
        query_words = [w.lower() for w in query.split() if len(w) > 2]
        scored_paragraphs = []
        
        for para in paragraphs:
            if len(para) < 20:  # Skip very short paragraphs
                continue
                
            para_lower = para.lower()
            score = 0
            
            # Score based on keyword matches
            for word in query_words:
                if word in para_lower:
                    score += 1
            
            # Bonus for longer, more informative paragraphs
            if len(para) > 100:
                score += 0.5
                
            if score > 0:
                scored_paragraphs.append((score, para))
        
        # Sort by relevance score
        scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
        
        # Build response from top relevant paragraphs
        if scored_paragraphs:
            # Take top 2-3 most relevant paragraphs
            top_paragraphs = [para for score, para in scored_paragraphs[:3]]
            response = '\n\n'.join(top_paragraphs)
            
            # Clean up response
            response = response.replace('  ', ' ').strip()
            
            # Limit length
            if len(response) > 800:
                response = response[:800] + '...'
                
            confidence = 0.7 if len(scored_paragraphs) > 1 else 0.5
        else:
            # Fallback: use first substantial paragraph
            for para in paragraphs:
                if len(para) > 50:
                    response = para[:400] + '...' if len(para) > 400 else para
                    confidence = 0.4
                    break
            else:
                response = context[:300] + '...' if len(context) > 300 else context
                confidence = 0.3

        return {
            'response': response,
            'confidence': confidence,
            'model': 'local_fallback'
        }
