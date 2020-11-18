# Examples of device controller commands

import controller
import logging

if __name__ == '__main__':
    print("Starting...")

    device = controller.Controller('/dev/ttyUSB0', logging_level=logging.DEBUG)
    print("Started.")

    res = device.set_pulse_generator(True)
    print(res)
    battery_level = device.read_battery()
    print("Battery level is: {}%".format(battery_level))
    res = device.set_pulse_generator(False)
    print(res)

    print("Test current range")
    res = device.set_current_range('high')
    print(res)
    res = device.set_current_range('low')
    print(res)

    print("Test voltage")
    res = device.set_voltage(150)
    print(res)
    res = device.set_voltage(70)
    print(res)
    res = device.set_voltage(85)
    print(res)

    print("Test num of n-plets")
    res = device.set_num_nplets(0)
    print(res)
    res = device.set_num_nplets(16777215)
    print(res)
    res = device.set_num_nplets(14500)
    print(res)

    print("Test time between pulses")
    res = device.set_time_between(1)
    print(res)
    res = device.set_time_between(254)
    print(res)
    res = device.set_time_between(126)
    print(res)

    print("Test delay")
    res = device.set_delay(0)
    print(res)
    res = device.set_delay(16777215)
    print(res)
    res = device.set_delay(5000)
    print(res)

    print("Test trigger")

    res = device.trigger_pulse_generator()
    print(res)

    print("Sleep for 5 seconds")
    #time.sleep(5)

    res = device.trigger_pulse_generator()
    print(res)

    print("Test n-plet repetition rate")
    res = device.set_repetition_rate(1)
    print(res)
    res = device.set_repetition_rate(400)
    print(res)

    print("Test pulse widths")
    res = device.set_pulse_width([50, 50])
    print(res)

    print("Test amplitude")
    res = device.set_amplitude([50, 50])
    print(res)

    print("Test mode")
    res = device.set_mode('unipolar')
    print(res)

    print("Test common electrode")
    res = device.set_common_electrode('anode')
    print(res)
    res = device.set_common_electrode('cathode')
    print(res)

    print("Test unipolar channels")
    res = device.set_pulses_unipolar(
        ['800000', '400000', '200000', '100000', '080000', '040000', '020000', '010000'], value_type='hex')
    print(res)
    """res = device.set_pulses_unipolar(
        [
            [24], [23], [22], [21], [20], [19], [18], [17], [16], [15], [14],
            [13], [12], [11], [10], [9], [8], [7], [6], [5], [4], [3], [2], [1]
        ], value_type='list'
    )"""
    res = device.set_pulses_unipolar(
        [
            [24], [23]
        ]
    )
    print(res)

    print("Change to bipolar")
    res = device.set_mode('bipolar')
    print(res)

    print("Test bipolar")
    res = device.set_pulses_bipolar(
        [('200000', '400000'), ('000001', '000002'), ('004000', '008000')], value_type='hex'
    )
    print(res)
    res = device.set_pulses_bipolar(
        [([22], [23]), ([1], [2]), ([15], [16])]
    )
    print(res)

    print("Set unipolar")
    res = device.set_mode('unipolar')
    print(res)

    print("Test short cathode&anode")
    res = device.set_common_electrode_short('cathode')
    print(res)
    res = device.set_common_electrode_short('anode')
    print(res)

    print("Test short output activity")
    res = device.set_output_channel_activity('000015', 50, value_type='hex')
    print(res)
    res = device.set_output_channel_activity([1,3,5], 50)
    print(res)

    device.close_serial()

    print("Quitting...")
