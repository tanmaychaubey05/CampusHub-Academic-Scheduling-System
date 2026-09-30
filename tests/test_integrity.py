"""
Unit tests for IntegrityService (Plagiarism and AI Code Detection).
"""

import unittest
from campushub.services.integrity_service import IntegrityService
from campushub.utils.exceptions import ValidationError


class TestIntegrityService(unittest.TestCase):
    def setUp(self):
        self.integrity_svc = IntegrityService(k_gram_size=3, window_size=4)

    def test_identical_plagiarism_detection(self):
        code1 = """
        def binary_search(arr, target):
            low = 0
            high = len(arr) - 1
            while low <= high:
                mid = (low + high) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    low = mid + 1
                else:
                    high = mid - 1
            return -1
        """
        # Exact copy with trivial whitespace/comments differences
        code2 = """
        # Search function implementation
        def binary_search(arr, target):
            low = 0
            high = len(arr) - 1
            while low <= high:
                mid = (low + high) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    low = mid + 1
                else:
                    high = mid - 1
            return -1
        """
        result = self.integrity_svc.calculate_plagiarism(code1, code2)
        self.assertGreaterEqual(result["similarity_percentage"], 90.0)
        self.assertEqual(result["verdict"], "High Plagiarism Risk")

    def test_distinct_code_low_similarity(self):
        code_dijkstra = """
        import heapq
        def dijkstra(graph, start):
            distances = {node: float('infinity') for node in graph}
            distances[start] = 0
            pq = [(0, start)]
            while pq:
                d, u = heapq.heappop(pq)
                for v, weight in graph[u].items():
                    if distances[u] + weight < distances[v]:
                        distances[v] = distances[u] + weight
                        heapq.heappush(pq, (distances[v], v))
            return distances
        """
        code_fibonacci = """
        def fibonacci(n):
            a, b = 0, 1
            seq = []
            for _ in range(n):
                seq.append(a)
                a, b = b, a + b
            return seq
        """
        result = self.integrity_svc.calculate_plagiarism(code_dijkstra, code_fibonacci)
        self.assertLess(result["similarity_percentage"], 20.0)
        self.assertEqual(result["verdict"], "Low Similarity (Acceptable)")

    def test_detect_ai_code_markers(self):
        ai_boilerplate_code = """
        # Step 1: Initialize helper function to process items
        # This function performs data validation
        def process_data(data):
            # Check if data is valid
            if not data:
                return None
            result = []
            for item in data:
                temp = item * 2
                result.append(temp)
            # Step 2: Return the result
            return result
        # Example usage:
        # result = process_data([1, 2, 3])
        """
        res = self.integrity_svc.detect_ai_code(ai_boilerplate_code)
        self.assertIn("ai_probability_percent", res)
        self.assertGreaterEqual(res["ai_probability_percent"], 40.0)

    def test_empty_content_validation(self):
        with self.assertRaises(ValidationError):
            self.integrity_svc.calculate_plagiarism("", "some code")
        with self.assertRaises(ValidationError):
            self.integrity_svc.detect_ai_code("   ")


if __name__ == "__main__":
    unittest.main()
