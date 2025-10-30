import Image from "next/image";

export default function Home() {
  return (
    testRichText()
  );
}

function testRichText() {
  return (
    <div>
      <p>This is a place to input text</p>
      <input type="text"/>
    </div>
  )
}
