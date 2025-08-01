/**
 * Comprehensive test suite for Phase 2 Collaboration Engine
 * Tests real-time collaboration, conflict resolution, and operational transformation
 */

class CollaborationEngineTestSuite {
    constructor() {
        this.testResults = [];
        this.collaborationEngine = new CollaborationEngine();
    }
    
    async runAllTests() {
        console.log('🧪 Starting Phase 2 Collaboration Engine Tests...');
        
        await this.testOperationalTransformation();
        await this.testConflictResolution();
        await this.testRealTimeSync();
        await this.testUndoRedo();
        await this.testUserPresence();
        await this.testCommentSystem();
        await this.testVersionControl();
        await this.testPerformance();
        
        this.printResults();
    }
    
    async testOperationalTransformation() {
        console.log('Testing Operational Transformation...');
        
        const testDoc = "Hello World";
        const user1Op = { type: 'insert', position: 5, content: ' Beautiful', documentId: 'doc1' };
        const user2Op = { type: 'insert', position: 11, content: '!', documentId: 'doc1' };
        
        // Apply operations concurrently
        const transformedOp1 = this.collaborationEngine.conflictResolver.transform(user1Op, [user2Op]);
        const transformedOp2 = this.collaborationEngine.conflictResolver.transform(user2Op, [user1Op]);
        
        const result1 = this.collaborationEngine.applyTransformedOperation(transformedOp1, testDoc);
        const result2 = this.collaborationEngine.applyTransformedOperation(transformedOp2, result1);
        
        const expected = "Hello Beautiful World!";
        
        this.assertEqual(
            result2,
            expected,
            'Operational Transformation',
            'Should correctly transform concurrent operations'
        );
    }
    
    async testConflictResolution() {
        console.log('Testing Conflict Resolution...');
        
        const testDoc = { revenue: 1000000, growth: 0.05 };
        const user1Op = { type: 'update', path: ['revenue'], value: 1200000, documentId: 'doc1' };
        const user2Op = { type: 'update', path: ['revenue'], value: 1100000, documentId: 'doc1' };
        
        const resolved = this.collaborationEngine.resolveConflict(user1Op, user2Op);
        
        this.assertEqual(
            resolved.value,
            1100000,
            'Conflict Resolution',
            'Should resolve conflicts with last-writer-wins strategy'
        );
    }
    
    async testRealTimeSync() {
        console.log('Testing Real-time Synchronization...');
        
        const mockWebSocket = new MockWebSocket();
        this.collaborationEngine.realtimeSync.websocket = mockWebSocket;
        
        const operation = { type: 'insert', position: 0, content: 'Test', documentId: 'doc1' };
        const userId = 'user123';
        
        this.collaborationEngine.realtimeSync.broadcastOperation(operation, userId);
        
        this.assertTrue(
            mockWebSocket.sentMessages.length > 0,
            'Real-time Sync',
            'Should broadcast operations via WebSocket'
        );
        
        const sentMessage = JSON.parse(mockWebSocket.sentMessages[0]);
        this.assertEqual(
            sentMessage.type,
            'operation',
            'Real-time Sync',
            'Should send correct message format'
        );
    }
    
    async testUndoRedo() {
        console.log('Testing Undo/Redo Functionality...');
        
        let document = "Hello";
        const userId = 'user123';
        
        // Insert operation
        const insertOp = { type: 'insert', position: 5, content: ' World', documentId: 'doc1' };
        document = this.collaborationEngine.applyOperation(insertOp, document, userId);
        
        this.assertEqual(
            document,
            "Hello World",
            'Undo/Redo',
            'Should apply insert operation'
        );
        
        // Undo
        document = this.collaborationEngine.undo(document, userId);
        this.assertEqual(
            document,
            "Hello",
            'Undo/Redo',
            'Should undo insert operation'
        );
        
        // Redo
        document = this.collaborationEngine.redo(document, userId);
        this.assertEqual(
            document,
            "Hello World",
            'Undo/Redo',
            'Should redo insert operation'
        );
    }
    
    async testUserPresence() {
        console.log('Testing User Presence...');
        
        const userId = 'user123';
        const userInfo = { name: 'John Doe', email: 'john@example.com' };
        
        this.collaborationEngine.addUser(userId, userInfo);
        
        this.assertTrue(
            this.collaborationEngine.activeUsers.has(userId),
            'User Presence',
            'Should add user to active users'
        );
        
        this.assertEqual(
            this.collaborationEngine.activeUsers.get(userId).name,
            'John Doe',
            'User Presence',
            'Should store user information correctly'
        );
        
        this.collaborationEngine.removeUser(userId);
        
        this.assertFalse(
            this.collaborationEngine.activeUsers.has(userId),
            'User Presence',
            'Should remove user from active users'
        );
    }
    
    async testCommentSystem() {
        console.log('Testing Comment System...');
        
        const documentId = 'doc1';
        const commentOp = {
            type: 'comment',
            commentId: 'comment1',
            text: 'This is a test comment',
            author: 'user123',
            timestamp: Date.now(),
            position: 10,
            documentId
        };
        
        let document = "Test document content";
        document = this.collaborationEngine.applyCommentOperation(commentOp, document);
        
        const comments = this.collaborationEngine.comments.get(documentId);
        
        this.assertTrue(
            comments && comments.length > 0,
            'Comment System',
            'Should add comments to document'
        );
        
        this.assertEqual(
            comments[0].text,
            'This is a test comment',
            'Comment System',
            'Should store comment text correctly'
        );
    }
    
    async testVersionControl() {
        console.log('Testing Version Control...');
        
        const document = { revenue: 1000000, ebitda: 200000 };
        const userId = 'user123';
        
        const snapshot = this.collaborationEngine.versionControl.createSnapshot(document, userId);
        
        this.assertTrue(
            snapshot.version >= 0,
            'Version Control',
            'Should create version snapshot'
        );
        
        this.assertEqual(
            snapshot.data.revenue,
            1000000,
            'Version Control',
            'Should store document data in snapshot'
        );
        
        const retrieved = this.collaborationEngine.versionControl.getSnapshotByVersion(snapshot.version);
        
        this.assertEqual(
            retrieved.data.revenue,
            1000000,
            'Version Control',
            'Should retrieve correct version'
        );
    }
    
    async testPerformance() {
        console.log('Testing Performance...');
        
        const startTime = performance.now();
        const iterations = 1000;
        
        for (let i = 0; i < iterations; i++) {
            const document = "Test document";
            const operation = { type: 'insert', position: 4, content: ' ' + i, documentId: 'doc1' };
            this.collaborationEngine.applyOperation(operation, document, 'user123');
        }
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.assertTrue(
            duration < 1000,
            'Performance',
            `Should handle ${iterations} operations in under 1 second (took ${duration}ms)`
        );
    }
    
    // Helper methods
    assertEqual(actual, expected, testName, message) {
        const passed = actual === expected;
        this.recordResult(testName, message, passed);
        
        if (!passed) {
            console.error(`❌ ${testName}: ${message} - Expected: ${expected}, Actual: ${actual}`);
        } else {
            console.log(`✅ ${testName}: ${message}`);
        }
    }
    
    assertTrue(condition, testName, message) {
        const passed = condition === true;
        this.recordResult(testName, message, passed);
        
        if (!passed) {
            console.error(`❌ ${testName}: ${message}`);
        } else {
            console.log(`✅ ${testName}: ${message}`);
        }
    }
    
    recordResult(testName, message, passed) {
        this.testResults.push({
            testName,
            message,
            passed,
            timestamp: new Date().toISOString()
        });
    }
    
    printResults() {
        console.log('\n📊 Test Results Summary:');
        console.log('========================');
        
        const passed = this.testResults.filter(r => r.passed).length;
        const total = this.testResults.length;
        
        console.log(`Total Tests: ${total}`);
        console.log(`Passed: ${passed}`);
        console.log(`Failed: ${total - passed}`);
        console.log(`Success Rate: ${((passed / total) * 100).toFixed(1)}%`);
        
        if (passed === total) {
            console.log('🎉 All tests passed!');
        } else {
            console.log('⚠️ Some tests failed. Check the detailed output above.');
        }
    }
}

// Mock WebSocket for testing
class MockWebSocket {
    constructor() {
        this.sentMessages = [];
        this.readyState = WebSocket.OPEN;
    }
    
    send(message) {
        this.sentMessages.push(message);
    }
    
    close() {
        this.readyState = WebSocket.CLOSED;
    }
}

// Run tests when DOM is ready
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', async () => {
        const testSuite = new CollaborationEngineTestSuite();
        await testSuite.runAllTests();
    });
}

// Export for Node.js testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CollaborationEngineTestSuite };
}
