const addBtn = document.getElementById('addNote');
const noteContainer = document.getElementById('noteContainer');

const note = `
<div class="box-border w-1/2 p-4 transition-all shadow-md min-h-24 rounded-xl bg-white/5">
        <input type="text" class="mb-2 text-xl font-bold bg-transparent border-b outline-none focus-visible:border-dotted" placeholder="Poznamka">
        <div>
        <img src="/content/avatar/259599177095315456" class="inline-block w-8 mt-0 mr-2 rounded-full">
        cyms
        </div>
        <textarea name="note-text" id="note-text" class="w-full p-2 my-2 transition-all rounded-lg shadow-inner outline-none resize-none bg-white/10" rows="10"></textarea>
        <div class="h-auto mt-2 mb-2">
            <a class="box-content px-3 py-2 transition-all border border-white rounded-md select-none hover:bg-white/10">Uložit</a>
        </div>
    </div>
`

addBtn.addEventListener('click', () => {noteContainer.innerHTML += note});