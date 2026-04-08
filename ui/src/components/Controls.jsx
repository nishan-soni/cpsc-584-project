export default function Controls() {


    const mappings = [
        { button: 'R2', action: 'Sprint' },
        { button: 'L2', action: 'Slow' },
        { button: '△', action: 'Look Over' },
        { button: '□', action: 'Take a Picture' },
    ];

    return (
        <div className="fixed inset-0 flex items-center justify-center z-50">
            <div className="bg-white/35 backdrop-blur-md border border-white/50 rounded-2xl p-8 w-80 shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
                <h2 className="text-2xl font-semibold mb-6 text-slate-900">Controller Mappings</h2>
                <div className="space-y-3">
                    {mappings.map((mapping, idx) => (
                        <div key={idx} className="flex justify-between items-center text-lg">
                            <span className="font-semibold text-gray-800">{mapping.button}</span>
                            <span className="text-gray-600">{mapping.action}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}