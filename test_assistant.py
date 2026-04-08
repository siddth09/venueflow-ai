"""
Test Suite for VenueFlow AI Assistant
Validates core functionality, decision-making, and Google integrations
"""

import unittest
from datetime import datetime, timedelta
from assistant import (
    VenueFlowAssistant,
    UserContext,
    VenueArea,
    CrowdLevel,
    AreaStatus,
    NavigationRoute
)
from google_integration import (
    GoogleMapsIntegration,
    FirebaseIntegration,
    GoogleCloudIntegration,
    GoogleServicesOrchestrator
)


class TestVenueFlowAssistant(unittest.TestCase):
    """Test core assistant functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.assistant = VenueFlowAssistant()
        self.test_user = UserContext(
            user_id="TEST_USER_001",
            seat_section="Section 105, Row 12, Seat 8",
            current_location=VenueArea.ENTRANCE_GATE,
            preferences={"food_preference": "vegetarian"},
            accessibility_needs=[]
        )
    
    def test_initialization(self):
        """Test assistant initializes correctly"""
        self.assertIsNotNone(self.assistant.venue_status)
        self.assertIsNotNone(self.assistant.event_timeline)
        self.assertEqual(len(self.assistant.venue_status), 7)
        self.assertGreater(len(self.assistant.event_timeline), 0)
    
    def test_venue_status_structure(self):
        """Test venue status has correct structure"""
        for area, status in self.assistant.venue_status.items():
            self.assertIsInstance(status, AreaStatus)
            self.assertIsInstance(status.crowd_level, CrowdLevel)
            self.assertGreaterEqual(status.wait_time_minutes, 0)
            self.assertGreaterEqual(status.capacity_percentage, 0)
            self.assertLessEqual(status.capacity_percentage, 100)
    
    def test_get_smart_recommendations(self):
        """Test smart recommendations generation"""
        recommendations = self.assistant.get_smart_recommendations(self.test_user)
        
        # Verify structure
        self.assertIn("timestamp", recommendations)
        self.assertIn("user_context", recommendations)
        self.assertIn("immediate_actions", recommendations)
        self.assertIn("timing_suggestions", recommendations)
        self.assertIn("alerts", recommendations)
        
        # Verify user context captured
        self.assertEqual(
            recommendations["user_context"]["seat_section"],
            self.test_user.seat_section
        )
    
    def test_optimal_route_calculation(self):
        """Test route calculation logic"""
        route = self.assistant.get_optimal_route(
            VenueArea.CONCESSION,
            VenueArea.SEATING,
            []
        )
        
        self.assertIsInstance(route, NavigationRoute)
        self.assertEqual(route.from_location, VenueArea.CONCESSION)
        self.assertEqual(route.to_location, VenueArea.SEATING)
        self.assertGreater(len(route.route_steps), 0)
        self.assertGreater(route.estimated_time_minutes, 0)
        self.assertGreaterEqual(route.crowd_score, 0)
    
    def test_accessibility_route_adjustment(self):
        """Test accessibility needs are reflected in routes"""
        standard_route = self.assistant.get_optimal_route(
            VenueArea.CONCESSION,
            VenueArea.SEATING,
            []
        )
        
        accessible_route = self.assistant.get_optimal_route(
            VenueArea.CONCESSION,
            VenueArea.SEATING,
            ["mobility"]
        )
        
        # Accessible route should not mention stairs
        for step in accessible_route.route_steps:
            self.assertNotIn("stairs", step.lower())
    
    def test_wait_time_prediction(self):
        """Test wait time prediction functionality"""
        prediction = self.assistant.predict_wait_times(VenueArea.CONCESSION, 15)
        
        self.assertIn("area", prediction)
        self.assertIn("current_wait_minutes", prediction)
        self.assertIn("predicted_wait_minutes", prediction)
        self.assertIn("confidence", prediction)
        self.assertIn("recommendation", prediction)
        
        # Predictions should be reasonable
        self.assertGreaterEqual(prediction["predicted_wait_minutes"], 0)
        self.assertLess(prediction["predicted_wait_minutes"], 60)
    
    def test_event_phase_detection(self):
        """Test event phase is correctly identified"""
        phase = self.assistant._get_current_event_phase()
        
        valid_phases = [
            "pre_game", "game_active", "halftime_approaching",
            "halftime", "game_ending", "post_game"
        ]
        self.assertIn(phase, valid_phases)
    
    def test_venue_heatmap_generation(self):
        """Test heatmap data generation"""
        heatmap = self.assistant.get_venue_heatmap()
        
        self.assertIn("timestamp", heatmap)
        self.assertIn("areas", heatmap)
        self.assertEqual(len(heatmap["areas"]), 7)
        
        # Verify each area has required fields
        for area in heatmap["areas"]:
            self.assertIn("area", area)
            self.assertIn("crowd_level", area)
            self.assertIn("capacity_percentage", area)
            self.assertIn("color_code", area)
            self.assertIn("wait_time", area)
    
    def test_natural_language_query_wait_time(self):
        """Test handling of wait time queries"""
        response = self.assistant.handle_query(
            "How long is the wait at concessions?",
            self.test_user
        )
        
        self.assertEqual(response["query_type"], "wait_times")
        self.assertIn("predictions", response)
    
    def test_natural_language_query_navigation(self):
        """Test handling of navigation queries"""
        response = self.assistant.handle_query(
            "How do I get to my seat?",
            self.test_user
        )
        
        self.assertEqual(response["query_type"], "navigation")
        self.assertIn("route", response)
        self.assertIn("estimated_arrival", response)
    
    def test_natural_language_query_facility(self):
        """Test handling of facility queries"""
        response = self.assistant.handle_query(
            "Where is the nearest restroom?",
            self.test_user
        )
        
        self.assertEqual(response["query_type"], "facility_info")
        self.assertEqual(response["facility"], "restroom")
        self.assertIn("current_status", response)
        self.assertIn("nearest_locations", response)
    
    def test_crowd_query_handling(self):
        """Test crowd-related queries"""
        response = self.assistant.handle_query(
            "Where is it least crowded?",
            self.test_user
        )
        
        self.assertEqual(response["query_type"], "crowd_status")
        self.assertIn("heatmap", response)
        self.assertIn("least_crowded", response)
    
    def test_recommendation_priority(self):
        """Test recommendations have appropriate priorities"""
        recommendations = self.assistant.get_smart_recommendations(self.test_user)
        
        for action in recommendations["immediate_actions"]:
            self.assertIn("priority", action)
            self.assertIn(action["priority"], ["low", "medium", "high"])


class TestGoogleIntegrations(unittest.TestCase):
    """Test Google services integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.maps = GoogleMapsIntegration()
        self.firebase = FirebaseIntegration()
        self.cloud = GoogleCloudIntegration()
        self.orchestrator = GoogleServicesOrchestrator()
    
    def test_google_maps_navigation(self):
        """Test Google Maps navigation integration"""
        nav_result = self.maps.get_indoor_navigation(
            from_coords={"latitude": 40.7589, "longitude": -73.9851},
            to_coords={"latitude": 40.7590, "longitude": -73.9850},
            accessibility_mode=False
        )
        
        self.assertIn("service", nav_result)
        self.assertIn("route", nav_result)
        self.assertIn("steps", nav_result["route"])
        self.assertGreater(len(nav_result["route"]["steps"]), 0)
    
    def test_google_maps_geolocation(self):
        """Test geolocation functionality"""
        location = self.maps.get_realtime_location("TEST_USER")
        
        self.assertIn("coordinates", location)
        self.assertIn("latitude", location["coordinates"])
        self.assertIn("longitude", location["coordinates"])
        self.assertIn("floor", location["coordinates"])
    
    def test_firebase_realtime_update(self):
        """Test Firebase realtime updates"""
        result = self.firebase.publish_venue_update(
            "concession",
            {"crowd_level": "moderate", "wait_time": 8}
        )
        
        self.assertEqual(result["service"], "Firebase Realtime Database")
        self.assertIn("subscribers_notified", result)
    
    def test_firebase_push_notification(self):
        """Test Firebase Cloud Messaging"""
        result = self.firebase.send_push_notification(
            user_tokens=["token1", "token2"],
            notification={
                "title": "Test Notification",
                "body": "This is a test"
            }
        )
        
        self.assertEqual(result["service"], "Firebase Cloud Messaging")
        self.assertEqual(result["recipients"], 2)
        self.assertEqual(result["delivery_status"], "sent")
    
    def test_firebase_user_preferences(self):
        """Test user preference retrieval"""
        prefs = self.firebase.get_user_preferences("TEST_USER")
        
        self.assertIn("preferences", prefs)
        self.assertIn("notifications_enabled", prefs["preferences"])
    
    def test_google_cloud_predictions(self):
        """Test Google Cloud ML predictions"""
        prediction = self.cloud.predict_crowd_flow([
            {"area": "concession", "crowd": 0.6}
        ])
        
        self.assertIn("predictions", prediction)
        self.assertIn("next_15_min", prediction["predictions"])
    
    def test_google_cloud_sentiment_analysis(self):
        """Test sentiment analysis"""
        result = self.cloud.analyze_sentiment(
            "The new navigation system is amazing!"
        )
        
        self.assertIn("sentiment", result)
        self.assertIn("score", result["sentiment"])
        self.assertGreater(result["sentiment"]["score"], 0)  # Positive sentiment
    
    def test_orchestrator_enhanced_navigation(self):
        """Test orchestrated navigation across services"""
        nav_result = self.orchestrator.get_enhanced_navigation(
            user_location={"user_id": "TEST_USER"},
            destination="Section 105",
            accessibility_needs=[]
        )
        
        self.assertIn("current_location", nav_result)
        self.assertIn("navigation", nav_result)
        self.assertIn("crowd_overlay", nav_result)
    
    def test_orchestrator_smart_notification(self):
        """Test smart notification logic"""
        result = self.orchestrator.send_smart_notification(
            user_id="TEST_USER",
            notification_type="wait_time_alert",
            data={"wait_time": 3, "previous_time": 10, "area": "Restroom"}
        )
        
        self.assertIn("service", result)
        self.assertEqual(result["service"], "Firebase Cloud Messaging")
    
    def test_orchestrator_ml_recommendations(self):
        """Test ML-powered recommendations"""
        ml_result = self.orchestrator.get_ml_powered_recommendations(
            user_context={"user_id": "TEST_USER"},
            venue_status={"concession_crowd": 0.6}
        )
        
        self.assertIn("immediate", ml_result)
        self.assertIn("ml_insights", ml_result)
    
    def test_orchestrator_feedback_processing(self):
        """Test feedback processing pipeline"""
        result = self.orchestrator.process_user_feedback(
            user_id="TEST_USER",
            feedback="Great experience! Very helpful."
        )
        
        self.assertIn("sentiment_analysis", result)
        self.assertIn("stored", result)
        self.assertTrue(result["stored"])


class TestSecurityAndValidation(unittest.TestCase):
    """Test security and input validation"""
    
    def setUp(self):
        self.assistant = VenueFlowAssistant()
        self.test_user = UserContext(
            user_id="TEST_USER",
            seat_section="Section 105",
            current_location=VenueArea.ENTRANCE_GATE
        )
    
    def test_invalid_venue_area_handling(self):
        """Test handling of invalid venue areas"""
        # Should not raise exception
        try:
            result = self.assistant.venue_status.get(None)
            self.assertIsNone(result)
        except Exception as e:
            self.fail(f"Should handle invalid area gracefully: {e}")
    
    def test_empty_query_handling(self):
        """Test handling of empty queries"""
        response = self.assistant.handle_query("", self.test_user)
        
        # Should return recommendations as fallback
        self.assertIn("timestamp", response)
    
    def test_user_context_defaults(self):
        """Test user context defaults are applied"""
        minimal_user = UserContext(
            user_id="MINIMAL",
            seat_section="Section 100"
        )
        
        self.assertIsNotNone(minimal_user.preferences)
        self.assertIsNotNone(minimal_user.accessibility_needs)
        self.assertEqual(len(minimal_user.accessibility_needs), 0)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        self.assistant = VenueFlowAssistant()
        self.test_user = UserContext(
            user_id="PERF_TEST",
            seat_section="Section 105",
            current_location=VenueArea.ENTRANCE_GATE
        )
    
    def test_recommendation_response_time(self):
        """Test recommendations generate quickly"""
        import time
        
        start = time.time()
        self.assistant.get_smart_recommendations(self.test_user)
        duration = time.time() - start
        
        # Should complete in under 1 second
        self.assertLess(duration, 1.0)
    
    def test_route_calculation_time(self):
        """Test route calculation performance"""
        import time
        
        start = time.time()
        self.assistant.get_optimal_route(
            VenueArea.ENTRANCE_GATE,
            VenueArea.SEATING,
            []
        )
        duration = time.time() - start
        
        # Should complete in under 0.5 seconds
        self.assertLess(duration, 0.5)
    
    def test_multiple_queries_performance(self):
        """Test handling multiple queries efficiently"""
        import time
        
        queries = [
            "Where is the restroom?",
            "How long is the wait?",
            "Navigate to my seat",
            "Where is it least crowded?",
            "When should I get food?"
        ]
        
        start = time.time()
        for query in queries:
            self.assistant.handle_query(query, self.test_user)
        duration = time.time() - start
        
        # Should handle all queries in under 2 seconds total
        self.assertLess(duration, 2.0)


class TestAccessibility(unittest.TestCase):
    """Test accessibility features"""
    
    def setUp(self):
        self.assistant = VenueFlowAssistant()
    
    def test_mobility_accessibility_routes(self):
        """Test mobility-accessible routing"""
        user_with_mobility_needs = UserContext(
            user_id="ACCESSIBLE_USER",
            seat_section="Section 105",
            current_location=VenueArea.ENTRANCE_GATE,
            accessibility_needs=["mobility"]
        )
        
        route = self.assistant.get_optimal_route(
            VenueArea.ENTRANCE_GATE,
            VenueArea.SEATING,
            user_with_mobility_needs.accessibility_needs
        )
        
        # Verify no stairs in route
        route_text = " ".join(route.route_steps).lower()
        self.assertNotIn("stairs", route_text)
    
    def test_accessible_facility_recommendations(self):
        """Test accessible facilities are prioritized"""
        user_with_needs = UserContext(
            user_id="ACCESSIBLE_USER",
            seat_section="Section 105",
            current_location=VenueArea.ENTRANCE_GATE,
            accessibility_needs=["mobility"]
        )
        
        recommendations = self.assistant.get_smart_recommendations(user_with_needs)
        
        # Should include accessibility information
        has_accessibility_info = any(
            "accessible" in str(action).lower()
            for action in recommendations["immediate_actions"]
        )
        self.assertTrue(has_accessibility_info)


def run_test_suite():
    """Run all tests and generate report"""
    print("="*70)
    print("VenueFlow AI Assistant - Test Suite")
    print("="*70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVenueFlowAssistant))
    suite.addTests(loader.loadTestsFromTestCase(TestGoogleIntegrations))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityAndValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestAccessibility))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Review output above.")
    
    return result


if __name__ == "__main__":
    run_test_suite()
