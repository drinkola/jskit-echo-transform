import unittest
from txmatch import BeginEndMatcher,NoIdInString
from txmatch import request_id
from txmatch import reformatLine

end_3b9d = "2010-06-19 20:55:58,552 [14] INFO  Geolearning.Web.GeoNext.GeoSessionModule - (CPD) {unauthenticated} ***OnEndRequest: CurrentURL: /geonext/cpd/stayAlive.geo, SessionID: 3b9db61a9f1f4feea3cb85e22ff8738d, Latency: 0.000, Blocked: 0.000, ElapsedTime: 0.031, Errors: 0, LoadedObjects: 6, PreFlushCount: 11, PostFlushCount: 1, FlushElapsed: 0.000 ***"

id_55a5 = ("10","55a5a725c1484fe1b86196c2c0806cac")
start_55a5 = "2010-06-19 00:00:01,086 [10] INFO  Geolearning.Web.GeoNext.GeoSessionModule - (Default Domain) {unauthenticated} ***OnBeginRequest: CurrentURL: /geonext/login.geo?ipmonitor, GET: , Role: unauthenticated, SessionID: 55a5a725c1484fe1b86196c2c0806cac ***"
reformatted_55a5 = "2010-06-19 00:00:01,086 55a5a725c1484fe1b86196c2c0806cac 10 unauthenticated /geonext/login.geo?ipmonitor"
end_55a5 = "2010-06-19 00:00:01,117 [10] INFO  Geolearning.Web.GeoNext.GeoSessionModule - (Default Domain) {unauthenticated} ***OnEndRequest: CurrentURL: /geonext/login.geo?ipmonitor, SessionID: 55a5a725c1484fe1b86196c2c0806cac, Latency: 0.000, Blocked: 0.000, ElapsedTime: 0.063, Errors: 0, LoadedObjects: 8, PreFlushCount: 21, PostFlushCount: 1, FlushElapsed: 0.000 ***"



class ExtractId(unittest.TestCase):
    def test_itCanGetTheId(self):
        self.assertEqual(
            tuple(id_55a5),
            request_id.search(start_55a5).groups()
        )

    def test_matchWorksForStartLine(self):
        sut = BeginEndMatcher()
        id = sut.get_request_id_for_line(start_55a5)
        self.assertEqual(id_55a5, id)

    def test_shouldThrowExceptionIfNoId(self):
        sut = BeginEndMatcher()
        self.assertRaises(
            NoIdInString, 
            lambda: sut.get_request_id_for_line("blah")
            )

class LineReformattingTest(unittest.TestCase):
    def test_shouldReformatLine(self):
        actual = reformatLine(start_55a5)
        expected = reformatted_55a5
        self.assertEqual(actual, expected)


class BeginLineSpotting(unittest.TestCase):

    def test_should_count_good_line(self):
        sut = BeginEndMatcher()
        sut.process( [start_55a5] )
        self.assertEqual(sut.on_begin_detected, 1)

    def test_shouldNotCountEmptyLine(self):
        sut = BeginEndMatcher()
        sut.process([""]) 
        self.assertEqual(sut.on_begin_detected, 0)

    def test_shouldNotCountLineWithoutMarker(self):
        sut = BeginEndMatcher()
        sut.process( ["line without marker"] )
        self.assertEqual(sut.on_begin_detected, 0)

class EndLineSpotting(unittest.TestCase):

    def test_shouldNotCountNonEndline(self):
        sut = BeginEndMatcher()
        sut.process( ["Nothing ends"] )
        self.assertEqual(sut.on_end_detected, 0)

    def test_shouldCountGoodEndline(self):
        sut = BeginEndMatcher()
        sut.process( [end_3b9d] )
        self.assertEqual(sut.on_end_detected, 1)

class MatchSpotting(unittest.TestCase):

    def test_IsIncompleteIfOnlyStartLineFound(self):
        sut = BeginEndMatcher()
        sut.process( [start_55a5] )
        starts = sut.incompleteRequests()
        self.assertEqual(starts, [reformatted_55a5])

    def test_ignoresOrphanedEnd(self):
        sut = BeginEndMatcher()
        sut.process( [end_3b9d] )
        ends =  sut.incompleteRequests()
        self.assertEqual(ends,[])

    def test_IsNotIncompleteIfBothStartAndEndFound(self):
        sut = BeginEndMatcher()
        sut.process([start_55a5, end_55a5])
        extras = sut.incompleteRequests()
        self.assertEquals(extras, [])

if __name__ == "__main__":
    unittest.main()
