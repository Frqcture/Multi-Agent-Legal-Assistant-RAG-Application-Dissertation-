import Image from "next/image";

export default function Home() {
  return (
    testRichText()
  );
}

function testRichText() {
  return (
    <div id="outerMainTextInput">
      <div id="innerMainTextInput">
        <p>This is a place to input text</p>
        <input id="promptTextBox" type="" name="prompt" value="Ask me a question..."/>
      </div>
    </div>
  )
}
