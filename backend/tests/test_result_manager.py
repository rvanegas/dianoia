import pytest
import time
from unittest.mock import patch, MagicMock
from services.agent_coordinator import coordinator, AgentResultManager, StoredAgentResult


class TestResultManager:
    """Test the result manager's handling of form evaluator results"""
    
    def test_result_manager_maintains_one_form_evaluator_when_complete(self):
        """Test that result manager maintains only one form evaluator result when all propositions are formalized"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Mock existing formalization results
        mock_existing_results = [
            StoredAgentResult(
                agent_type='formalizer',
                operation='formalize_proposition',
                result_content={
                    'proposition': 'Socrates is a man',
                    'ascii': 'P(a)'
                },
                confidence=0.9,
                reasoning='Formalized proposition',
                target_metadata={'target_type': 'proposition', 'target_content': 'Socrates is a man'},
                snapshot_id='test_snapshot',
                processed_at=time.time()
            ),
            StoredAgentResult(
                agent_type='formalizer',
                operation='formalize_proposition',
                result_content={
                    'proposition': 'All men are mortal',
                    'ascii': 'forall x. (P(x) -> Q(x))'
                },
                confidence=0.9,
                reasoning='Formalized proposition',
                target_metadata={'target_type': 'proposition', 'target_content': 'All men are mortal'},
                snapshot_id='test_snapshot',
                processed_at=time.time()
            ),
            StoredAgentResult(
                agent_type='formalizer',
                operation='formalize_proposition',
                result_content={
                    'proposition': 'Socrates is mortal',
                    'ascii': 'Q(a)'
                },
                confidence=0.9,
                reasoning='Formalized proposition',
                target_metadata={'target_type': 'proposition', 'target_content': 'Socrates is mortal'},
                snapshot_id='test_snapshot',
                processed_at=time.time()
            )
        ]
        
        # Add the existing formalization results to the result manager first
        for result in mock_existing_results:
            result_manager.add_result(conversation_id, result)
        
        # Add a form evaluator result
        form_evaluator_result = StoredAgentResult(
            agent_type='form_evaluator',
            operation='evaluate_propositions',
            result_content={
                'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                'evaluation': {
                    'proposition_evaluations': [
                        {'proposition': 'Socrates is a man', 'truth_value': 0.5},
                        {'proposition': 'All men are mortal', 'truth_value': 0.5},
                        {'proposition': 'Socrates is mortal', 'truth_value': 0.5}
                    ],
                    'argument_validity': 1.0
                }
            },
            confidence=0.8,
            reasoning='Evaluated formal argument',
            target_metadata={'target_type': 'argument', 'target_content': None},
            snapshot_id='test_snapshot',
            processed_at=time.time()
        )
        
        result_manager.add_result(conversation_id, form_evaluator_result)
        
        # Verify the result was added
        results = result_manager.get_results(conversation_id)
        form_evaluator_results = [r for r in results if r.agent_type == 'form_evaluator']
        assert len(form_evaluator_results) == 1
        
        # Add another form evaluator result (should replace the first)
        new_form_evaluator_result = StoredAgentResult(
            agent_type='form_evaluator',
            operation='evaluate_propositions',
            result_content={
                'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                'evaluation': {
                    'proposition_evaluations': [
                        {'proposition': 'Socrates is a man', 'truth_value': 0.5},
                        {'proposition': 'All men are mortal', 'truth_value': 0.5},
                        {'proposition': 'Socrates is mortal', 'truth_value': 0.5}
                    ],
                    'argument_validity': 0.8  # Different validity
                }
            },
            confidence=0.8,
            reasoning='Updated formal evaluation',
            target_metadata={'target_type': 'argument', 'target_content': None},
            snapshot_id='test_snapshot',
            processed_at=time.time()
        )
        
        result_manager.add_result(conversation_id, new_form_evaluator_result)
        
        # Verify only one form evaluator result remains
        results = result_manager.get_results(conversation_id)
        form_evaluator_results = [r for r in results if r.agent_type == 'form_evaluator']
        assert len(form_evaluator_results) == 1
        assert form_evaluator_results[0].result_content['evaluation']['argument_validity'] == 0.8
    
    def test_result_manager_removes_form_evaluator_when_incomplete(self):
        """Test that result manager removes form evaluator results when no formalizations exist"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # No existing formalization results (incomplete)
        mock_existing_results = []
        
        # Add a form evaluator result (this shouldn't exist but let's test cleanup)
        form_evaluator_result = StoredAgentResult(
            agent_type='form_evaluator',
            operation='evaluate_propositions',
            result_content={
                'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                'evaluation': {
                    'proposition_evaluations': [
                        {'proposition': 'Socrates is a man', 'truth_value': 0.5},
                        {'proposition': 'All men are mortal', 'truth_value': 0.5},
                        {'proposition': 'Socrates is mortal', 'truth_value': 0.5}
                    ],
                    'argument_validity': 1.0
                }
            },
            confidence=0.8,
            reasoning='Formal evaluation without formalizations',
            target_metadata={'target_type': 'argument', 'target_content': None},
            snapshot_id='test_snapshot',
            processed_at=time.time()
        )
        
        # Add the result - it should be removed during the add process due to no formalizations
        result_manager.add_result(conversation_id, form_evaluator_result)
        
        # Verify the result was removed due to no formalizations
        results = result_manager.get_results(conversation_id)
        form_evaluator_results = [r for r in results if r.agent_type == 'form_evaluator']
        assert len(form_evaluator_results) == 0
    
    def test_result_manager_maintains_content_evaluator_independently(self):
        """Test that result manager maintains content evaluator results independently"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add a content evaluator result
        content_evaluator_result = StoredAgentResult(
            agent_type='content_evaluator',
            operation='evaluate_propositions',
            result_content={
                'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                'evaluation': {
                    'proposition_evaluations': [
                        {'proposition': 'Socrates is a man', 'truth_value': 0.9},
                        {'proposition': 'All men are mortal', 'truth_value': 0.95},
                        {'proposition': 'Socrates is mortal', 'truth_value': 0.9}
                    ],
                    'argument_validity': 0.95
                }
            },
            confidence=0.9,
            reasoning='Content evaluation',
            target_metadata={'target_type': 'argument', 'target_content': None},
            snapshot_id='test_snapshot',
            processed_at=time.time()
        )
        
        result_manager.add_result(conversation_id, content_evaluator_result)
        
        # Verify the content evaluator result was added
        results = result_manager.get_results(conversation_id)
        content_evaluator_results = [r for r in results if r.agent_type == 'content_evaluator']
        assert len(content_evaluator_results) == 1
        
        # Add another content evaluator result (should replace the first)
        new_content_evaluator_result = StoredAgentResult(
            agent_type='content_evaluator',
            operation='evaluate_propositions',
            result_content={
                'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                'evaluation': {
                    'proposition_evaluations': [
                        {'proposition': 'Socrates is a man', 'truth_value': 0.8},
                        {'proposition': 'All men are mortal', 'truth_value': 0.85},
                        {'proposition': 'Socrates is mortal', 'truth_value': 0.8}
                    ],
                    'argument_validity': 0.85
                }
            },
            confidence=0.85,
            reasoning='Updated content evaluation',
            target_metadata={'target_type': 'argument', 'target_content': None},
            snapshot_id='test_snapshot',
            processed_at=time.time()
        )
        
        result_manager.add_result(conversation_id, new_content_evaluator_result)
        
        # Verify only one content evaluator result remains
        results = result_manager.get_results(conversation_id)
        content_evaluator_results = [r for r in results if r.agent_type == 'content_evaluator']
        assert len(content_evaluator_results) == 1
        assert content_evaluator_results[0].result_content['evaluation']['argument_validity'] == 0.85


if __name__ == "__main__":
    pytest.main([__file__]) 