Blockly.Blocks['Turn_right_1_step'] = {
  init: function () {
    this.jsonInit({
      type: 'Turn_right_1_step',
      message0: '%{BKY_TURN_RIGHT_1_STEP}',
      previousStatement: null,
      nextStatement: null,
      colour: '#48BCBC',
      toolip: '',
      helpUrl: '',
    });
  }
};

Blockly.Lua['Turn_right_1_step'] = function (block) {
  const code = [
    'MOTOrigid16(30,30,30,65,65,65,65,65,30,30,30,65,65,65,65,65)',
    'MOTOsetspeed(30)',
    'MOTOmove16(80, 30, 100, 100, 93, 55, 124, 100, 120, 170, 100, 100, 107, 145, 76, 100)',
    'MOTOwait()',
    'MOTOsetspeed(24)',
    'MOTOmove16(80, 30, 85, 95, 123, 55, 154, 95, 120, 170, 85, 105, 137, 145, 106, 105)',
    'MOTOwait()',
    'MOTOsetspeed(24)',
    'MOTOmove16(80, 30, 100, 100, 93, 55, 124, 100, 120, 170, 100, 100, 107, 145, 76, 100)',
    'MOTOwait()',
    'MOTOsetspeed(30)',
    'MOTOmove16(80, 30, 100, 100, 93, 55, 124, 100, 120, 170, 100, 100, 107, 145, 76, 100)',
    'MOTOwait()',
    '',
  ];
  return code.join('\n');
}

Blockly.Python['Turn_right_1_step'] = function (block) {
  var code = "base_action.action('" + Blockly.Msg['TURN_RIGHT_1_STEP'] + "')\n";
  return code;
}

