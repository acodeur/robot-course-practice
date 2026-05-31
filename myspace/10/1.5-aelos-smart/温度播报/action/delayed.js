Blockly.Blocks['delayed'] = {
  init: function () {
    this.jsonInit({
      type: 'delayed',
      message0: '%{BKY_DELAY} %1 %{BKY_SECOND_DELAY_TIME}',
      args0: [
        {
          type: 'field_number',
          name: 'time',
          value: 0,
          min: 0,
          max: 5000,
          precision: 0.1,
        },
      ],
      previousStatement: null,
      nextStatement: null,
      colour: Blockly.Msg.ControlHUE,
      tooltip: '',
      helpUrl: '',
    });
  }
};

Blockly.Lua['delayed'] = function(block) {
  let time = parseInt(block.getFieldValue("time"), 0);
  const MAX_TIME = 5000;
  const ms = 1000;
  time = time * ms;
  if (time > MAX_TIME) {
    time = MAX_TIME;
  }
  let code = `DelayMs(${time})\n`;
  return code;
}

Blockly.Python['delayed'] = function (block) {
  const time = block.getFieldValue('time') || 0;
  Blockly.Python.definitions_['import_time'] = 'import time';
  const code = `time.sleep(${time})\n`;
  return code;
}

