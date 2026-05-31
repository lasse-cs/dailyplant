const CharacterCounter = ({ getEditorState }) => {
  const editorState = getEditorState();
  const content = editorState.getCurrentContent();
  const text = content.getPlainText();

  const textLength = text ? text.length : 0;

  return window.React.createElement('div', {
    className: 'w-inline-block w-tabular-nums w-help-text w-mr-4',
  }, `Characters: ${textLength}`);
}

window.draftail.registerPlugin({
  type: 'characters',
  meta: CharacterCounter,
}, 'controls');