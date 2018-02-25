import time
import unittest
from tempfile import NamedTemporaryFile

from octoprint_octolapse.extruder import ExtruderTriggers
from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.trigger import TimerTrigger


class Test_TimerTrigger(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        self.OctoprintPrinterProfile = self.CreateOctoprintPrinterProfile()

    def tearDown(self):
        del self.Settings
        del self.OctoprintPrinterProfile

    def CreateOctoprintPrinterProfile(self):
        return dict(
            volume=dict(
                width=250,
                depth=200,
                height=200,
                formFactor="Not A Circle",
                custom_box=False,
            )
        )

    def test_TimerTrigger(self):
        """Test the timer trigger"""
        # use a short trigger time so that the test doesn't take too long
        self.Settings.CurrentSnapshot().timer_trigger_seconds = 2
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        trigger = TimerTrigger(self.Settings)
        trigger.ExtruderTriggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None,
                                                    None)  # Ignore extruder
        trigger.RequireZHop = False  # no zhop required
        trigger.HeightIncrement = 0  # Trigger on any height change
        # test initial state
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # set interval time to 0, send another command and test again (should not trigger, no homed axis)
        trigger.IntervalSeconds = 0
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Home all axis and try again with interval seconds 1 - should not trigger since the timer will start after the home command
        trigger.IntervalSeconds = 2
        position.Update("g28")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # send another command and try again, should not trigger cause we haven't waited 2 seconds yet
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Set the last trigger time to 1 before the previous LastTrigger time(equal to interval seconds), should not trigger
        trigger.TriggerStartTime = time.time() - 1.01
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Set the last trigger time to 1 before the previous LastTrigger time(equal to interval seconds), should trigger
        trigger.TriggerStartTime = time.time() - 2.01
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

    def test_TimerTrigger_ExtruderTriggers(self):
        """Test All Extruder Triggers"""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # home the axis
        position.Update("G28")
        trigger = TimerTrigger(self.Settings)
        trigger.IntervalSeconds = 1
        trigger.RequireZHop = False  # no zhop required

        # Reset the extruder

        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # Try on extruding start - previous position not homed, do not trigger
        trigger.ExtruderTriggers = ExtruderTriggers(
            True, None, None, None, None, None, None, None, None, None)
        position.Extruder.IsExtrudingStart = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # send another command, now the previous state has been homed, should trigger
        position.Update("AnotherCommandNowPreviousHomed")
        # set is extruding start, wont be set by the above command!
        position.Extruder.IsExtrudingStart = True
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)
        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on extruding
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, True, None, None, None, None, None, None, None, None)
        position.Extruder.IsExtruding = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on primed
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, True, None, None, None, None, None, None, None)
        position.Extruder.IsPrimed = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on retracting start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, True, None, None, None, None, None, None)
        position.Extruder.IsRetractingStart = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on retracting
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, True, None, None, None, None, None)
        position.Extruder.IsRetracting = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on partially retracted
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, True, None, None, None, None)
        position.Extruder.IsPartiallyRetracted = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on retracted
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, True, None, None, None)
        position.Extruder.IsRetracted = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on detracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, True, None, None)
        position.Extruder.IsDetractingStart = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on detracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, None, True, None)
        position.Extruder.IsDetracting = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Reset the extruder
        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        trigger.IsWaiting = True
        # try out on detracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, None, None, True)
        position.Extruder.IsDetracted = True
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

    def test_TimerTrigger_ExtruderTriggerWait(self):
        """Test wait on extruder"""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # home the axis
        position.Update("G28")
        trigger = TimerTrigger(self.Settings)
        trigger.RequireZHop = False  # no zhop required
        trigger.IntervalSeconds = 1

        # Reset the extruder

        position.Extruder.Reset()
        position.Extruder.IsPrimed = False
        # Use on extruding start for this test.
        trigger.ExtruderTriggers = ExtruderTriggers(
            True, None, None, None, None, None, None, None, None, None)
        position.Extruder.IsExtrudingStart = False
        trigger.TriggerStartTime = time.time() - 1.01
        # will not wait or trigger because the previous position state was not homed
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # send another command and try again
        position.Update("PreviousPositionIsNowHomed")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # update again with no change
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)
        # set the trigger and try again
        position.Extruder.IsExtrudingStart = True
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

    def test_TimerTrigger_LayerChange_ZHop(self):
        """Test the layer trigger for layer changes triggers"""
        self.Settings.CurrentSnapshot().timer_trigger_require_zhop = True
        self.Settings.CurrentPrinter().z_hop = .5
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        trigger = TimerTrigger(self.Settings)
        trigger.ExtruderTriggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None,
                                                    None)  # Ignore extruder
        trigger.IntervalSeconds = 1
        # test initial state
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # send commands that normally would trigger a layer change, but without all axis homed.
        position.Update("g0 x0 y0 z.2 e1")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # Home all axis and try again, wait on zhop
        position.Update("g28")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)
        position.Update("g0 x0 y0 z.2 e1")
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # try zhop
        position.Update("g0 x0 y0 z.7 ")

        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # extrude on current layer, no trigger (wait on zhop)
        position.Update("g0 x0 y0 z.7 e1")
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # do not extrude on current layer, still waiting
        position.Update("g0 x0 y0 z.7 ")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # partial hop, but close enough based on our printer measurement tolerance (0.005)
        position.Update("g0 x0 y0 z1.1999")
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)

        # creat wait state
        position.Update("g0 x0 y0 z1.3 e1")
        trigger.TriggerStartTime = time.time() - 1.01
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # move down (should never happen, should behave properly anyway)
        position.Update("g0 x0 y0 z.8")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # move back up to current layer (should NOT trigger zhop)
        position.Update("g0 x0 y0 z1.3")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # move up a bit, not enough to trigger zhop
        position.Update("g0 x0 y0 z1.79749")
        trigger.Update(position)
        self.assertFalse(trigger.IsTriggered(0))
        self.assertTrue(trigger.IsWaiting)

        # move up a bit, just enough to trigger zhop
        position.Update("g0 x0 y0 z1.79751")
        trigger.Update(position)
        self.assertTrue(trigger.IsTriggered(0))
        self.assertFalse(trigger.IsWaiting)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test_TimerTrigger)
    unittest.TextTestRunner(verbosity=3).run(suite)
